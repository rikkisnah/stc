#!/usr/bin/env bash
# Run the training categorization workflow via Codex.
set -euo pipefail

usage() {
    echo "Usage: $0 [codex exec args]"
    echo ""
    echo "Runs the ticket categorization training workflow using Codex."
    echo "Reads the prompt from prompts/train-to-categorize-tickets-prompt.md."
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Any additional arguments are forwarded to 'codex exec'."
    exit 0
}

[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && usage

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROMPT_FILE="$REPO_ROOT/prompts/train-to-categorize-tickets-prompt.md"
CODEX_BIN="${CODEX_BIN:-codex}"

if ! command -v "$CODEX_BIN" >/dev/null 2>&1; then
    echo "Error: codex CLI is not installed or not on PATH." >&2
    exit 1
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "Error: prompt file '$PROMPT_FILE' not found." >&2
    exit 1
fi

cd "$REPO_ROOT"

"$CODEX_BIN" \
    --sandbox workspace-write \
    -a on-failure \
    exec \
    -C "$REPO_ROOT" \
    "$@" \
    < "$PROMPT_FILE"
