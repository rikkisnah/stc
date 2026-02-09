## Project Memory

- Add `ai-assisted` in all code documentation to indicate AI was used
- `data-schemes.md` now documents the schemas for `rule-engine.csv` and `tickets-categorized.csv` so the LLM understands what each dataset represents.
- Training work happens directly within `scripts/trained-data/` (no dated subdirectories); maintain the operator’s local context when snapshotting files but keep all live files in this shared directory.

## Archives

- Retired runners live in `scripts/archives/`.
- Retired/older prompts live in `prompts/archives/`.
- Treat archives as reference-only; prefer current entrypoints under `scripts/` and prompts under `prompts/`.
