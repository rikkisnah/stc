P# TASKS.md

## States
- `[ready]` — Defined, waiting for tests
- `[in-test]` — Test engineer writing failing tests
- `[in-impl]` — Implementer writing production code
- `[in-review]` — Reviewer validating
- `[done]` — Tests green, verified, closed

---

## Active Tasks
### Task 1: Add Project Key column to rule-engine template [in-impl]
- **Behavior:** Insert a `Project Key` column into `templates/rule-engine.csv` (and document it) so templates drive project-aware rule definitions.
- **Acceptance:** Template headers and schema docs list the new column immediately after rule identifiers; csv diff shows only the added column.
- **Scope:** `templates/rule-engine.csv`, `templates/data-schemes.md`.

### Task 2: Document golden artifact immutability gate [ready]
- **Behavior:** Codify in docs and tasking that `scripts/trained-data/golden-rules-engine/` is never modified by automated steps and only updated via audited promotion.
- **Acceptance:** `TASKS.md` and/or `docs/` clearly state the gate and reviewers have a checklist item to validate no golden file diffs.
- **Scope:** `TASKS.md`, `docs/`, `README.md`.

### Task 3: Propagate Project Key to working rule engine output [ready]
- **Behavior:** Update `scripts/trained-data/rule-engine.csv` to include and populate `Project Key` for all existing rules.
- **Acceptance:** CSV header includes `Project Key` and every non-header row has a non-empty value.
- **Scope:** `scripts/trained-data/rule-engine.csv`.

---

## Completed

<!-- Move [done] tasks here to keep the active list clean -->
