#!/usr/bin/env bash
# Analyze all normalized tickets in batches via Codex.
set -euo pipefail

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Analyzes all normalized tickets in batches using Codex."
    echo "Each batch is a separate Codex invocation so the context window stays fresh."
    echo "Progress is tracked via tickets-categorized.csv — tickets already present are skipped."
    echo ""
    echo "Options:"
    echo "  --batch-size N    Tickets per batch (default: 10)"
    echo "  --codex-arg ARG   Forward ARG to 'codex' (top-level)"
    echo "  --exec-arg ARG    Forward ARG to 'codex exec'"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Any other arguments are forwarded to 'codex exec'."
    exit 0
}

REPO_ROOT="/mnt/data/src/rkisnah/stc"
PROMPT_FILE="$REPO_ROOT/prompts/analyze-all-tickets-prompt.md"
WORK_DIR="$REPO_ROOT/scripts/trained-data"
CATEGORIZED="$WORK_DIR/tickets-categorized.csv"
CODEX_BIN="${CODEX_BIN:-codex}"
BATCH_SIZE=10

CODEX_TOP_ARGS=()
CODEX_EXEC_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --codex-arg)
            CODEX_TOP_ARGS+=("$2")
            shift 2
            ;;
        --exec-arg)
            CODEX_EXEC_ARGS+=("$2")
            shift 2
            ;;
        *)
            CODEX_EXEC_ARGS+=("$1")
            shift
            ;;
    esac
done

if ! command -v "$CODEX_BIN" >/dev/null 2>&1; then
    echo "Error: codex CLI is not installed or not on PATH." >&2
    exit 1
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "Error: prompt file '$PROMPT_FILE' not found." >&2
    exit 1
fi

cd "$REPO_ROOT"

mkdir -p "$WORK_DIR"

if [[ ! -f "$CATEGORIZED" ]]; then
    cp "$REPO_ROOT/templates/tickets-categorized.csv" "$CATEGORIZED"
    echo "Initialized blank tickets-categorized.csv"
fi

if [[ ! -f "$WORK_DIR/rule-engine.csv" ]]; then
    cp "$WORK_DIR/golden-rules-engine/rule-engine.csv" "$WORK_DIR/rule-engine.csv"
    echo "Copied golden rule-engine.csv as working baseline"
fi

mapfile -t ALL_TICKETS < <(find "$REPO_ROOT/scripts/normalized-tickets" -name '*.json' | sort)

TOTAL=${#ALL_TICKETS[@]}
if [[ $TOTAL -eq 0 ]]; then
    echo "No ticket JSON files found in scripts/normalized-tickets/."
    exit 0
fi

echo "Found $TOTAL total ticket files. Batch size: $BATCH_SIZE"

BATCH_NUM=0
while true; do
    DONE_TICKETS=()
    if [[ -f "$CATEGORIZED" ]]; then
        while IFS=, read -r ticket _rest; do
            [[ "$ticket" == "Ticket" ]] && continue
            DONE_TICKETS+=("$ticket")
        done < "$CATEGORIZED"
    fi

    PENDING=()
    for json_file in "${ALL_TICKETS[@]}"; do
        ticket_id="$(basename "$json_file" .json)"
        skip=false
        for done_id in "${DONE_TICKETS[@]}"; do
            if [[ "$done_id" == "$ticket_id" ]]; then
                skip=true
                break
            fi
        done
        if [[ "$skip" == false ]]; then
            PENDING+=("$json_file")
        fi
    done

    REMAINING=${#PENDING[@]}
    if [[ $REMAINING -eq 0 ]]; then
        echo ""
        echo "All $TOTAL tickets have been categorized."
        break
    fi

    BATCH=("${PENDING[@]:0:$BATCH_SIZE}")
    BATCH_NUM=$((BATCH_NUM + 1))
    BATCH_COUNT=${#BATCH[@]}

    echo ""
    echo "=== Batch $BATCH_NUM: processing $BATCH_COUNT tickets ($REMAINING remaining) ==="

    TICKET_LIST=""
    for f in "${BATCH[@]}"; do
        TICKET_LIST+="- $f"$'\n'
    done

    # codex exec reads the initial prompt either from an argument or stdin.
    # We feed a combined prompt on stdin: base instructions + this batch's ticket list.
    {
        cat "$PROMPT_FILE"
        echo ""
        echo "Categorize the following $BATCH_COUNT tickets. Read each JSON file, evaluate against the rule engine, and append results to scripts/trained-data/tickets-categorized.csv. Do NOT process any other tickets."
        echo ""
        printf '%s' "$TICKET_LIST"
    } | "$CODEX_BIN" \
        "${CODEX_TOP_ARGS[@]}" \
        exec \
        --sandbox workspace-write \
        -C "$REPO_ROOT" \
        "${CODEX_EXEC_ARGS[@]}"

    echo "Batch $BATCH_NUM complete."
done

echo ""
echo "Analysis finished. Results in: $CATEGORIZED"
