# Repository Guidelines

## Project Overview

DC Ops Ticket Categorization (STC) — an LLM-assisted pipeline that classifies DC Ops incident tickets into structured failure categories using a mix of rule-based matching and LLM reasoning.

## Directory Layout

- `scripts/` — Python scripts for ticket ingestion and normalization. Each script should have a brief usage comment at the top.
  - `get-tickets.py` — fetches raw JSON from Jira → `scripts/tickets-json/`
  - `normalize-tickets.py` — normalizes per-ticket JSON → `scripts/normalized-tickets/<date>/`
  - `scripts/archives/` — retired runner scripts kept for reference (not the primary entrypoints)
- `templates/` — CSV templates (headers only). Used as starting skeletons for new training sessions. **Not a working directory.**
  - `rule-engine.csv` — header-only template
  - `tickets-categorized.csv` — header-only template
  - `data-schemes.md` — schema definitions for rule engine and categorized tickets
- `scripts/trained-data/` — **Working directory** for each training session. All reads and writes happen here.
  - `rule-engine.csv` — live working copy of rules for the session
  - `tickets-categorized.csv` — live working copy of categorized tickets
  - `rule-engine-N.csv`, `tickets-categorized-N.csv` — pass-suffixed archival snapshots
- `scripts/trained-data/golden-rules-engine/` — **Read-only.** The authoritative, production-ready rule engine and category definitions. Only updated manually by a human after audit is complete.
  - `rule-engine.csv` — production rule engine
  - `category-of-issues.md` — canonical failure category definitions
- `prompts/` — LLM prompts
  - `train-to-categorize-tickets-prompt.md` — the primary training/categorization prompt (session setup, ticket selection, rule evaluation, snapshots)
  - `update-rule-engine-prompt.md` — update/extend the rule engine from feedback
  - `prompts/archives/` — retired prompts kept for reference

## Training Pipeline

1. `scripts/get-tickets.py` → raw JSON from Jira → `scripts/tickets-json/`
2. `scripts/normalize-tickets.py` → normalized per-ticket JSON → `scripts/normalized-tickets/<date>/`
3. LLM categorization / rule updates → `scripts/trained-data/tickets-categorized.csv` + `scripts/trained-data/rule-engine.csv`
4. Human audit → pass snapshots (`tickets-categorized-N.csv`, `rule-engine-N.csv`)
5. Final merged output → `scripts/trained-data/golden-rules-engine/rule-engine.csv` (read-only, manually copied)

## Key Rules

- **All artifacts go under `scripts/`** — scripts resolve output paths relative to their own directory, never the repo root. No script should create files at the repo root.
- **Never modify** files in `scripts/trained-data/golden-rules-engine/` — that directory is read-only and manually updated by a human.
- **Never write working data to `templates/`** — templates are header-only skeletons.
- All session work goes in `scripts/trained-data/`.
- Training batches use 5 tickets per pass.
- When rules fire, record all `RuleID`s and propagate the maximum rule confidence into the CSV's `LLM Confidence` column. LLM-generated classifications continue to use their own reported confidence scores.
- Automatically set `Human Audit for Accuracy = needs-review` whenever the effective confidence is below 0.5; otherwise default to `pending-review` until the auditor updates it.

## Audit Regression Workflow

After a human audits a training pass, use the current rule-update workflow (`prompts/update-rule-engine-prompt.md`) or refer to archived prompts under `prompts/archives/`.
1. Copy audited `rule-engine-<N>.csv` over the live `rule-engine.csv`.
2. Reset `tickets-categorized.csv` to header-only.
3. Re-run categorization on the same tickets.
4. Compare re-run output to audited `tickets-categorized-<N>.csv` field-by-field.
5. All match → regression-stable, eligible for golden promotion.
6. Divergences → archive as next suffix, fix rules, repeat until stable.

## Commit & Pull Request Guidelines

- Follow conventional commits (`feat:`, `fix:`, `chore:`, etc.). Keep each commit logically scoped.
- Reference an issue number in the PR description and summarize the change.
