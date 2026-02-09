# DC Ops Ticket Categorization Workflow

This document captures the step-by-step workflow from the training prompt so auditors and operators can repeat or validate each pass consistently.

## 1. Session Setup
- Use the shared `scripts/trained-data/` directory as the active working location.
- Ensure `scripts/trained-data/` exists; create it if necessary.
- Copy `templates/tickets-categorized.csv` into `scripts/trained-data/` as the blank working ledger.
- Copy `scripts/trained-data/golden-rules-engine/rule-engine.csv` into the same directory as the working rule baseline.
- From this point onward, only read/write the working copies inside `scripts/trained-data/`.

## 2. Ticket Selection
- Use normalized inputs from `scripts/normalized-tickets/`.
- Filter to tickets with `status.current = Resolved` that are not already present in the working `tickets-categorized.csv`.
- Randomly sample exactly **five** tickets for each training pass (the process always handles five at a time).

## 3. Categorization Pass
- For each ticket, evaluate existing rules in `scripts/trained-data/rule-engine.csv`.
  - If a rule matches, record all matching `RuleID` values in the CSV row, set `Categorization Source = rule`, and populate `LLM Confidence` with the highest confidence value among the triggering rules.
  - If no rule matches, apply LLM reasoning, set `Categorization Source = llm`, include a confidence score, and describe the rationale.
- When LLM reasoning reveals a reusable pattern, append a new rule to the working `rule-engine.csv` with the next sequential `RuleID`, an appropriate confidence, and `Created By = llm`.
- Always flag `Runbook Present = TRUE` when rules `R011`, `R012`, `R015`, or other runbook cues fire (e.g., “Prescriptive Action” titles or runbook phrases in comments).
- Write every processed ticket to `scripts/trained-data/tickets-categorized.csv`. Auto-set `Human Audit for Accuracy = needs-review` when the computed confidence is below 0.5; otherwise default to `pending-review` until a human reviewer updates it.

## 4. Human Audit Loop
- Auditor reviews the live `tickets-categorized.csv`, updates `Human Audit for Accuracy` (`Accurate`, `Unknown`, or `Incorrect`), and adds `Human Comments` as needed.
- Based on audit outcomes, adjust `rule-engine.csv`:
  - Increase confidence and set `Created By = human-confirmed` for accurate rules.
  - Leave confidence unchanged for unknown verdicts.
  - Refine or remove rules that were marked incorrect.
  - Encode any new human-provided heuristics as fresh rules.

## 5. Snapshots and Re-runs
- After every five-ticket batch (or after audit changes), snapshot both working files as `tickets-categorized-<pass>.csv` and `rule-engine-<pass>.csv` to preserve history.
- To rerun a batch, delete or archive the affected rows in the live working file, then repeat the categorization steps using the same normalized inputs and rules.

## 6. Promotion to Golden Rule Engine
- Once all passes are audited and approved, a human manually copies the vetted `rule-engine.csv` into `scripts/trained-data/golden-rules-engine/rule-engine.csv`.
- The golden directory remains read-only during training; updates only flow from audited working files after approval.

Following this sequence ensures every training pass is reproducible, reviewable, and ready for audit or reprocessing on the original normalized ticket set.

## 7. Auditor Regression Workflow
The human-in-the-loop validation cycle uses the following repeatable steps:
1. Run the prompt against the working `rule-engine.csv` (copied from the golden baseline) and a blank `tickets-categorized.csv` for the day.
2. Immediately snapshot both outputs as `rule-engine-1.csv` and `tickets-categorized-1.csv`.
3. Audit those snapshots for accuracy and rule quality.
4. After audit fixes, copy `rule-engine-1.csv` back to the live `rule-engine.csv`.
5. Re-run the prompt, ensuring `tickets-categorized.csv` has been reset to just the header row before processing.
6. Compare the new results to the audited snapshot; if they match, promote `rule-engine.csv` to the golden directory manually.
7. If the comparison fails, archive the attempt as `rule-engine-3.csv` / `tickets-categorized-3.csv` (or the next available suffix) for review.
8. Repeat the audit + rerun loop until the working output matches the audited expectation.
