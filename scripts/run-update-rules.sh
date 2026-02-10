#!/usr/bin/env bash
# Update the rule engine interactively via Codex.
set -euo pipefail

usage() {
    echo "Usage: $0 [codex args]"
    echo ""
    echo "Opens an interactive session to update the golden rule engine."
    echo "Describe ticket patterns and the LLM will add the appropriate rules."
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    exit 0
}

[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && usage

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROMPT_FILE="$REPO_ROOT/prompts/update-rule-engine-prompt.md"
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

# Interactive mode: pass the prompt as the initial message.
"$CODEX_BIN" \
    --sandbox workspace-write \
    -C "$REPO_ROOT" \
    "$@" \
    "$(cat "$PROMPT_FILE")"
