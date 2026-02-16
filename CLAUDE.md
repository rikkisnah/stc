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

DC Ops Ticket Categorization (STC) — primary goal: based on HPC/DO ticket data, predict the correct `Category of Issue` and `Category`. The pipeline combines rule-based matching with LLM-assisted rule generation and improves over repeated human-audit feedback cycles.

### Directory Layout

- `scripts/` — Python runners for ticket ingestion (`get_tickets.py`) and normalization (`normalize_tickets.py`). Each script starts with a brief usage comment. Retired runners live under `scripts/archives/`.
- `wireframe-ui/` — Next.js UX surface for local pipeline execution previews (JQL-driven) and run telemetry (live logs, commands, heartbeat, cancel, timestamps).
- `templates/` — Header-only CSV templates (`rule-engine.csv`, `tickets-categorized.csv`) and schema docs (`data-schemes.md`). Never write working data here.
- `scripts/trained-data/` — Working directory for live training passes (`rule-engine.csv`, `tickets-categorized.csv`, plus numbered snapshots). `scripts/trained-data/golden-rules-engine/` is read-only and holds the audited production rules plus `category-of-issues.md`.
- `prompts/` — LLM prompts for training and rule updates (`training.md`). Archives reside in `prompts/archives/`.

### Training Pipeline

1. `scripts/get_tickets.py` → raw Jira JSON → `scripts/tickets-json/`.
2. `scripts/normalize_tickets.py` → normalized per-ticket JSON → `scripts/normalized-tickets/<date>/`.
3. LLM categorization + rule updates → `scripts/trained-data/tickets-categorized.csv` & `scripts/trained-data/rule-engine.csv`.
4. Human audit → snapshot copies (`tickets-categorized-N.csv`, `rule-engine-N.csv`).
5. Golden promotion → manual copy into `scripts/trained-data/golden-rules-engine/rule-engine.csv`.

### Key Rules

- Keep every artifact under `scripts/`; no script should emit files at repo root.
- Never modify files in `scripts/trained-data/golden-rules-engine/` without an audited promotion.
- Training batches operate on 5 tickets per pass; record all `RuleID`s that fire and propagate the maximum rule confidence to `LLM Confidence`.
- Assign `Human Audit for Accuracy = needs-review` when confidence < 0.5; otherwise default to `pending-review` until audit.
- During human audit, edit only `Human Audit for Accuracy` and `Human Comments`; do not edit `Human Audit Guidance`.
- Human audit final values are `correct` or `incorrect` (pipeline pre-audit values are `pending-review` and `needs-review`).
- For `needs-review` rows with `uncategorized`, auditors should usually set `incorrect` with a concrete correction note unless the issue is truly unknown.
- Use `docs/human-audit-playbook.md` for row-level audit instructions and examples.

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

### Python Coverage Requirement

- For any newly added or modified Python code, accompanying tests must keep coverage at `100%` for the affected Python module(s) under `scripts/`.

## Coverage & Test Completeness Policy

- Every task must ship with tests in the same change set.
- For modified Python modules, the corresponding test suite must drive changed-module coverage to 100% (line coverage), or the PR must include an explicit exception in the task notes explaining why full coverage is not feasible.
- Required workflow:
  1. Add or update tests before/alongside implementation (TDD order).
  2. Run the smallest affected test set first.
  3. Run coverage for affected modules and confirm no untested lines remain.
- Any branch left untested without a justified exception is considered incomplete.

## UX Workflow Rules

- UX code in `wireframe-ui/` must remain frontend-first; do not block visual review on backend service integration.
- For JQL-triggered UX runs, keep script artifacts confined under `scripts/analysis/ui-runs/`.
- Preserve cancel semantics: cancel must stop active script execution and attempt artifact cleanup for that run.
- Any UX behavior changes must include tests in `wireframe-ui/__tests__/` and keep `npm test` green.
- Any change under `wireframe-ui/` MUST run `make ui-verify` before task handoff/review; this is a blocking quality gate.
- `make ui-verify` is the required runtime guard because it clears `.next`, runs a clean build, runs runtime smoke against the built app (`UI_SMOKE_MODE=start`) for runtime/chunk module errors, and then runs Playwright E2E.
- If `make ui-verify` fails (including `Cannot find module`/runtime overlay signatures), the task remains `[in-impl]` until fixed and re-verified.
- Hydration-sensitive changes (timestamps/random data/locale formatting) require running Playwright E2E (`make ui-e2e`).
