#!/usr/bin/env bash
# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted
set -euo pipefail

START_DATE=""
END_DATE=""
JQL_FILE="scripts/jql/hpc_default.jql"
RULE_ENGINE="scripts/trained-data/rule-engine.local.csv"
OUTPUT_DIR="scripts/analysis"
PROMPT_FILE="prompts/training.md"
CODEX_TIMEOUT="120"
CODEX_BATCH_SIZE="2"
MAX_REVIEW_ROWS="200"
ASSUME_YES="false"

usage() {
  cat <<'EOF'
Usage:
  scripts/run_training_loop.sh --start-date YYYY-MM-DD --end-date YYYY-MM-DD [options]

Options:
  --start-date DATE        Required start date.
  --end-date DATE          Required end date.
  --jql-file PATH          JQL file path (default: scripts/jql/hpc_default.jql).
  --rule-engine PATH       Rule engine CSV path (default: scripts/trained-data/rule-engine.local.csv).
  --output-dir PATH        Output analysis dir (default: scripts/analysis).
  --prompt-file PATH       Prompt file for run_training.py (default: prompts/training.md).
  --codex-timeout SEC      Codex timeout for run_training.py (default: 120).
  --codex-batch-size N     Codex batch size for run_training.py (default: 2).
  --max-review-rows N      Max review rows for run_training.py (default: 200).
  -y, --yes                Skip interactive confirmations in Python scripts.
  -h, --help               Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start-date)
      START_DATE="${2:-}"
      shift 2
      ;;
    --end-date)
      END_DATE="${2:-}"
      shift 2
      ;;
    --jql-file)
      JQL_FILE="${2:-}"
      shift 2
      ;;
    --rule-engine)
      RULE_ENGINE="${2:-}"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="${2:-}"
      shift 2
      ;;
    --prompt-file)
      PROMPT_FILE="${2:-}"
      shift 2
      ;;
    --codex-timeout)
      CODEX_TIMEOUT="${2:-}"
      shift 2
      ;;
    --codex-batch-size)
      CODEX_BATCH_SIZE="${2:-}"
      shift 2
      ;;
    --max-review-rows)
      MAX_REVIEW_ROWS="${2:-}"
      shift 2
      ;;
    -y|--yes)
      ASSUME_YES="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$START_DATE" || -z "$END_DATE" ]]; then
  echo "Error: --start-date and --end-date are required." >&2
  usage >&2
  exit 2
fi

YES_ARGS=()
if [[ "$ASSUME_YES" == "true" ]]; then
  YES_ARGS=(-y)
fi

echo "[1/3] Fetching tickets..."
uv run python3 scripts/get_tickets.py \
  -a "$START_DATE" "$END_DATE" \
  --include-resolved-only \
  --jql-file "$JQL_FILE" \
  "${YES_ARGS[@]}"

echo "[2/3] Normalizing tickets..."
uv run python3 scripts/normalize_tickets.py --input-dir scripts/tickets-json/ "${YES_ARGS[@]}"

echo "[3/3] Categorizing with rule engine..."
uv run python3 scripts/rule_engine_categorize.py \
  --rule-engine "$RULE_ENGINE" \
  --output-dir "$OUTPUT_DIR" \
  "${YES_ARGS[@]}"

echo "Done. Next:"
echo "1) Audit $OUTPUT_DIR/tickets-categorized.csv"
echo "2) Run training with:"
echo "uv run python3 scripts/run_training.py \\"
echo "  --tickets-categorized $OUTPUT_DIR/tickets-categorized.csv \\"
echo "  --rules-engine-file $RULE_ENGINE \\"
echo "  --prompt-file $PROMPT_FILE \\"
echo "  --codex-timeout $CODEX_TIMEOUT \\"
echo "  --codex-batch-size $CODEX_BATCH_SIZE \\"
echo "  --max-review-rows $MAX_REVIEW_ROWS \\"
if [[ "$ASSUME_YES" == "true" ]]; then
  echo "  --yes"
else
  echo "  # add --yes to skip confirmation prompt"
fi
