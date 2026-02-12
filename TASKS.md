# TASKS.md

## States
- `[ready]` — Defined, waiting for tests
- `[in-test]` — Test engineer writing failing tests
- `[in-impl]` — Implementer writing production code
- `[in-review]` — Reviewer validating
- `[done]` — Tests green, verified, closed

---

## Active Tasks

### Task 1: Ticket ingestion script health checks [ready]
- **Behavior:** Ensure `scripts/get-tickets.py` validates environment configuration and emits usage instructions up top.
- **Acceptance:** pytest suite covers env var validation; script prints usage when run with `-h` or missing config.
- **Scope:** `scripts/get-tickets.py`, potential fixtures under `tests/`.
- **Notes:** Keep outputs confined to `scripts/tickets-json/`.

### Task 2: Categorization confidence guardrails [ready]
- **Behavior:** Enforce confidence propagation and audit flagging rules inside `scripts/trained-data/tickets-categorized.csv` generation pipeline.
- **Acceptance:** Regression tests confirm max rule confidence is applied and low confidence rows flip to `needs-review`.
- **Scope:** `scripts/normalize-tickets.py`, prompt logic, csv helpers.
- **Notes:** Align with MEMORY.md constraints.

---

## Completed

<!-- Move [done] tasks here to keep the active list clean -->
