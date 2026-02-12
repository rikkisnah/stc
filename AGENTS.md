# AGENTS.md — TDD Workflow Orchestration

## Overview

This STC repository applies a strict TDD workflow across the DC Ops Ticket Categorization pipeline, pairing role-based skills with subagents so Jira ingestion scripts, normalization utilities, and LLM training runs all stay in lockstep.

## Roles

| Role | Skill | Subagent | Owns | STC Focus |
|---|---|---|---|---|
| Architect | /architect | @architect | TASKS.md, MEMORY.md | Breaks down ticket-processing work, curates prompts, keeps directory rules aligned. |
| Test Engineer | /test-engineer | @test-engineer | tests/ | Crafts or updates regression suites for scripts and prompt flows before implementation. |
| Implementer | /implementer | @implementer | scripts/, prompts/ | Modifies ingestion/normalization scripts and prompt assets to satisfy failing tests. |
| Reviewer | /reviewer | @reviewer | verdicts only | Confirms tests, audits CSV outputs, and enforces policy gates. |

## Task Lifecycle

```
[ready] → [in-test] → [in-impl] → [in-review] → [done]
                                        ↓ (fail)
                                     [in-impl]
```

## When to Use Skills vs Subagents

- **Skill** — Pull the role’s instructions into the current conversation (e.g., `/architect`) when you need guidance inline with other work.
- **Subagent** — Spin up the corresponding subagent (e.g., `@architect`) when you want that role to work independently without polluting the main thread.

## Workflow Sequence

1. **Architect** decomposes user requests into granular, testable TASKS.md entries and keeps MEMORY.md aligned with project constraints.
2. **Test Engineer** writes or updates failing tests that cover ticket ingestion, normalization, or CSV generation behaviors for `[ready]` tasks.
3. **Implementer** updates scripts, prompts, or rules to satisfy the failing tests and keep artifacts in `scripts/trained-data/` coherent.
4. **Reviewer** validates outputs (including CSV diffs) and either advances tasks to `[done]` or bounces them back to `[in-impl]` for fixes.

## MEMORY.md Governance

- Only the architect edits sections above the `---` divider.
- Other roles append proposals under `## Proposals` using `[role] YYYY-MM-DD — text`.
- Architect reviews, merges, and clears proposals before kicking off a fresh cycle.

## File Permissions Matrix

| Path/Area | Architect | Test Engineer | Implementer | Reviewer |
|---|---|---|---|---|
| `TASKS.md` | read/write | state only | state only | state only |
| `MEMORY.md` | read/write | proposals | proposals | proposals |
| `scripts/` (ingestion + normalization) | plan | test fixtures | read/write | read |
| `scripts/trained-data/` | plan snapshots | seed regression data | read/write CSVs | audit diffs |
| `prompts/` | curate | test prompt hooks | edit prompts | review wording |
| `templates/` | reference | reference | read-only | reference |
| `docs/` | read/write | read | read | read |

## Repository Operating Rules

### Project Overview

DC Ops Ticket Categorization (STC) — an LLM-assisted pipeline that classifies DC Ops incident tickets into structured failure categories using rule-based matching plus LLM reasoning.

### Directory Layout

- `scripts/` — Python runners for ticket ingestion (`get-tickets.py`) and normalization (`normalize-tickets.py`). Each script starts with a brief usage comment. Retired runners live under `scripts/archives/`.
- `templates/` — Header-only CSV templates (`rule-engine.csv`, `tickets-categorized.csv`) and schema docs (`data-schemes.md`). Never write working data here.
- `scripts/trained-data/` — Working directory for live training passes (`rule-engine.csv`, `tickets-categorized.csv`, plus numbered snapshots). `scripts/trained-data/golden-rules-engine/` is read-only and holds the audited production rules plus `category-of-issues.md`.
- `prompts/` — LLM prompts for training (`train-to-categorize-tickets-prompt.md`) and rule updates (`update-rule-engine-prompt.md`). Archives reside in `prompts/archives/`.

### Training Pipeline

1. `scripts/get-tickets.py` → raw Jira JSON → `scripts/tickets-json/`.
2. `scripts/normalize-tickets.py` → normalized per-ticket JSON → `scripts/normalized-tickets/<date>/`.
3. LLM categorization + rule updates → `scripts/trained-data/tickets-categorized.csv` & `scripts/trained-data/rule-engine.csv`.
4. Human audit → snapshot copies (`tickets-categorized-N.csv`, `rule-engine-N.csv`).
5. Golden promotion → manual copy into `scripts/trained-data/golden-rules-engine/rule-engine.csv`.

### Key Rules

- Keep every artifact under `scripts/`; no script should emit files at repo root.
- Never modify files in `scripts/trained-data/golden-rules-engine/` without an audited promotion.
- Training batches operate on 5 tickets per pass; record all `RuleID`s that fire and propagate the maximum rule confidence to `LLM Confidence`.
- Assign `Human Audit for Accuracy = needs-review` when confidence < 0.5; otherwise default to `pending-review` until audit.

### Audit Regression Workflow

1. After audit, copy `rule-engine-<N>.csv` over the live `rule-engine.csv`.
2. Reset `tickets-categorized.csv` to headers only.
3. Re-run categorization on the audited ticket set.
4. Compare fresh output to `tickets-categorized-<N>.csv` field-by-field.
5. If all fields match, mark the pass regression-stable and consider for golden promotion; otherwise archive as the next suffix and iterate.

### Commit & Pull Request Guidelines

- Follow conventional commits (`feat:`, `fix:`, `chore:`, etc.) with logically scoped changes.
- Reference the relevant issue in PR descriptions and summarize the change set plus validation (tests, audits, CSV diffs).

## Code Generation Policy

All generated code MUST include:

- Tag: `#ai-assisted`
- Disclaimer in file header comment:
```
  # Code was generated via OCI AI and was reviewed by a human SDE
  # Tag: #ai-assisted
```
- Apply to: all new source files, test files, and scripts
- Format: use the comment syntax appropriate to the language (# for Python/bash, // for JS/TS, /* */ for CSS, etc.)
