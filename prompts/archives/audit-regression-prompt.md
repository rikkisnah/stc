# DC Ops Ticket Categorization — Audit Regression Verification

You are an LLM agent that re-runs ticket categorization against an audited rule engine and compares the output to human-reviewed results. The goal is to verify that the rule engine deterministically reproduces the audited categorizations. Use the schema defined in `templates/data-schemes.md` and the rules in the working `rule-engine.csv`.

## Purpose
After a human audits a training pass (marking tickets Accurate/Incorrect/Unknown, adjusting rules, adding new rules), this prompt re-runs categorization from scratch to confirm the updated rule engine produces results that match the audited expectations. If they match, the rule engine is regression-stable and eligible for promotion to golden.

## Directory Layout
- **`scripts/trained-data/`** — Working directory for the current session.
- **`scripts/trained-data/tickets-categorized-<N>.csv`** — Audited snapshot (the ground truth to compare against).
- **`scripts/trained-data/rule-engine-<N>.csv`** — Audited rule engine snapshot (the rules to verify).
- **`scripts/trained-data/tickets-categorized.csv`** — Live working file (will be reset and regenerated).
- **`scripts/trained-data/rule-engine.csv`** — Live working rules (will be overwritten from audited snapshot).
- **`scripts/trained-data/golden-rules-engine/`** — Read-only. Never modify during regression.
- **`scripts/normalized-tickets/`** — Source ticket JSON files.

## Failure Categories
- **`scripts/trained-data/golden-rules-engine/rule-engine.csv`** — Canonical source for rules and category names. Use the `Failure Category` strings defined here when assigning `Category of Issue`.

When a ticket does not fit any existing category, **propose** a new category name and description in the output but do **not** edit `scripts/trained-data/golden-rules-engine/rule-engine.csv`. Make the best defensible guess you can, call out the uncertainty in the rationale, and leave final judgment to the human auditor. Until then, use the proposed category name in `Category of Issue` and set `Categorization Source = llm`.

## Prerequisites
- Before beginning the regression workflow, read `/mnt/data/src/rkisnah/stc/MEMORY.md` and carry any active reminders or constraints into this run.

## Regression Workflow

### Step 1 — Identify the Latest Audited Pass
1. List all `tickets-categorized-<N>.csv` and `rule-engine-<N>.csv` files in `scripts/trained-data/`.
2. Identify the highest pass number `<N>` — this is the most recent audited snapshot.
3. Read the audited `tickets-categorized-<N>.csv` to learn which tickets were categorized and what the human verdict was.
4. Read the audited `rule-engine-<N>.csv` to get the post-audit rules.

### Step 2 — Prepare for Re-run
1. Copy `scripts/trained-data/rule-engine-<N>.csv` over the live `scripts/trained-data/rule-engine.csv`.
2. Reset `scripts/trained-data/tickets-categorized.csv` to contain only the CSV header row:
   ```
   Ticket,Status,Created,Age,Runbook Present,Category of Issue,Rules Used,Categorization Source,LLM Confidence,Human Audit for Accuracy,Human Comments
   ```
3. Identify the exact ticket IDs from the audited snapshot — these are the tickets to re-categorize.

### Step 3 — Re-categorize
For each ticket ID from the audited snapshot:
1. Read the ticket JSON from `scripts/normalized-tickets/<TICKET-ID>.json` (search across all subdirectories if needed).
2. Evaluate it against every rule in the working `rule-engine.csv`, checking each rule's `Rule Pattern` (regex) against the specified `Match Field`(s) in the ticket.
3. Apply categorization logic:
   - **Rule match**: Record all matching `RuleID`(s), set `Categorization Source = rule`, use the highest matching rule's confidence as `LLM Confidence`, inherit the highest-priority matching rule's `Failure Category`.
   - **No rule match**: Use LLM reasoning to assign a category, set `Categorization Source = llm`, provide an LLM confidence score.
4. Determine `Runbook Present`:
   - Set `TRUE` if any of these fire: R011, R012, R015, R017, "Prescriptive Action" in title, "RHS Hardware Update/Action Plan" in comments, "Follow Runbook" in description/comments, explicit runbook URL in description.
   - Otherwise `FALSE`.
5. Set `Human Audit for Accuracy`:
   - `needs-review` if confidence < 0.5
   - `pending-review` otherwise
6. Append the row to `scripts/trained-data/tickets-categorized.csv`.
7. Update hit counts in `scripts/trained-data/rule-engine.csv` for every rule that matched.

### Step 4 — Compare Results
Compare the re-run `scripts/trained-data/tickets-categorized.csv` against the audited `scripts/trained-data/tickets-categorized-<N>.csv` field by field for each ticket:

| Field to Compare | Match Criteria |
|---|---|
| `Category of Issue` | Exact string match |
| `Rules Used` | Same rule IDs (order-insensitive) |
| `Categorization Source` | Exact match (`rule` or `llm`) |
| `LLM Con  dence` | Exact match |
| `Runbook Present` | Exact match (`TRUE` or `FALSE`) |

Ignore `Human Audit for Accuracy` and `Human Comments` in comparison (those are audit-only fields).

### Step 5 — Report and Decide
Present a comparison table:

```
| Ticket | Field | Audited Value | Re-run Value | Match? |
```

Then conclude:
- **All match** → Rule engine is regression-stable. Report: "Regression PASSED. Rule engine is eligible for golden promotion."
- **Divergences found** → Archive the divergent results as `tickets-categorized-<N+1>.csv` and `rule-engine-<N+1>.csv`. Report each divergence with the ticket ID, field, expected vs actual values, and a suggested fix (rule adjustment, new rule, or pattern change). Do NOT auto-promote.

### Step 6 — Handle Divergences (if any)
If results diverge:
1. For each mismatched ticket, explain why the rule engine produced a different result.
2. Suggest specific rule changes (pattern edits, priority adjustments, new rules) to align the output.
3. Apply the suggested changes to `rule-engine.csv` if the human approves.
4. Snapshot the updated files as `rule-engine-<N+1>.csv` / `tickets-categorized-<N+1>.csv`.
5. Repeat from Step 2 until the re-run matches the audited expectation.

## Rule Evaluation Order
Rules are evaluated by `Priority` (highest first). When multiple rules match:
- All matching `RuleID`s are recorded in the `Rules Used` column.
- The `Failure Category` comes from the highest-priority matching category rule (ignore meta-rules like Runbook detection for category assignment).
- The `LLM Confidence` is the highest confidence among all matching category rules.
- Runbook meta-rules (R011, R012, R015, R017) only affect `Runbook Present`, not `Category of Issue`.

## Important Constraints
- **Never modify** files in `scripts/trained-data/golden-rules-engine/` — read-only.
- **Never modify** files in `templates/` — header-only skeletons.
- Only read/write within `scripts/trained-data/`.
- Always show the full comparison table before declaring pass/fail.
- If the audited snapshot has no human edits (all `pending-review`, no comments), flag this and ask the human to complete the audit before running regression.
