# DC Ops Ticket Categorization — Train from Human Feedback

You are an LLM agent that reads a human-audited `tickets-categorized.csv` and updates the `rule-engine.csv` to reflect the auditor's corrections. You do **not** categorize tickets yourself — that was already done by the rule engine. Your job is to learn from the human's feedback and improve the rules.

## Context

The upstream workflow is:
1. `rule-engine-categorize.py` applied the rule engine to all normalized tickets and wrote `scripts/analysis/tickets-categorized.csv`.
2. A human reviewed that CSV, filling in `Human Audit for Accuracy` (`correct`, `incorrect`, or `needs-review`) and `Human Comments` with corrections or notes.
3. **You start here.** Read the audited CSV, interpret the feedback, and update the rule engine.

## Directory Layout
- **`scripts/analysis/`** — Working directory. Contains the audited `tickets-categorized.csv` and the working `rule-engine.csv`.
- **`scripts/trained-data/golden-rules-engine/rule-engine.csv`** — Read-only baseline. **Never modify.**
- **`scripts/normalized-tickets/`** — Source ticket JSON files (read-only).
- **`templates/`** — Header-only skeletons. **Never write here.**

## Prerequisites
- Before beginning, read `/mnt/data/src/rkisnah/stc/MEMORY.md` and carry any active reminders or constraints into this session.
- Read `templates/data-schemes.md` for the CSV schemas.

## Workflow

### Step 1 — Load Current State
1. Read `scripts/analysis/rule-engine.csv` (the working rules).
2. Read `scripts/analysis/tickets-categorized.csv` (the human-audited results).
3. Identify all tickets where `Human Audit for Accuracy` has been filled in (i.e., is not `pending-review` or empty). These are the feedback rows to process.
4. If no feedback rows exist, report "No human feedback found" and stop.

### Step 2 — Process Feedback

For each audited ticket, act based on the verdict:

#### `correct` — Rule Confirmed
- If `Categorization Source = rule`:
  - For each rule in `Rules Used`, increase confidence toward 1.0 (cap at 0.95 unless already higher) and set `Created By = human-confirmed`.
  - Increment `Hit Count`.
- If `Categorization Source = none` (was uncategorized) and the human marked it `correct`:
  - The human accepted "uncategorized" — no rule change needed. Skip.

#### `incorrect` — Human Corrected
The human's `Human Comments` field contains the correction. Parse it to determine what changed:
1. **Wrong category**: The human provided the correct `Category of Issue` in comments.
   - Read the ticket JSON to understand what text should have matched.
   - Check if an existing rule should have fired but didn't (pattern too narrow) → widen the pattern.
   - Check if a rule fired incorrectly (pattern too broad or priority wrong) → narrow the pattern, lower priority, or remove the rule.
   - If no existing rule covers the correct category, propose a new rule.
2. **Wrong Runbook Present**: Adjust meta-rules (R011, R012, R015, R017) or add new meta-rule patterns.
3. **Multiple corrections**: Process each correction independently.

#### `needs-review` — Still Pending
- Skip. Do not modify rules for tickets still under review.

### Step 3 — Create New Rules
When creating a new rule from human feedback:
1. Read the source ticket JSON to identify the distinguishing text pattern.
2. Choose the most specific regex that matches this ticket without being so narrow it's single-use.
3. Test the proposed regex mentally against other tickets you've seen — flag if it might over-match.
4. Assign the next sequential `RuleID` (e.g., if the highest existing ID is R018, use R019).
5. Set `Confidence = 0.8`, `Created By = human-feedback`, `Hit Count = 1`.
6. Set `Priority` relative to existing rules — more specific patterns get higher priority.
7. Choose the appropriate `Match Field` based on where the distinguishing text appears.

### Step 4 — Adjust Existing Rules
When modifying an existing rule:
- **Widen pattern**: Add alternation (`|`) to catch the missed case. Keep the original pattern intact.
- **Narrow pattern**: Add negative lookahead or additional required terms to prevent false positives.
- **Lower priority**: If a broad rule is stealing matches from a more specific one, reduce its priority.
- **Remove rule**: If a rule is fundamentally wrong (human overrode it multiple times), remove it entirely. Log the removal.
- **Never** lower confidence below 0.5 — remove the rule instead.

### Step 5 — Snapshot and Report

1. Write the updated rules to `scripts/analysis/rule-engine.csv`.
2. Snapshot both files:
   - `scripts/analysis/rule-engine-<N>.csv` (next available suffix)
   - `scripts/analysis/tickets-categorized-<N>.csv` (copy of the audited input)
3. Print a structured summary:

```
=== Training from Human Feedback — Summary ===

Tickets reviewed: <count>
  correct:   <count>
  incorrect: <count>
  needs-review (skipped): <count>

Rules confirmed (confidence bumped): <list of RuleIDs>
Rules modified: <list of RuleIDs with description of change>
Rules removed:  <list of RuleIDs with reason>
Rules created:  <list of new RuleIDs with pattern and category>

Next step: Run rule-engine-categorize.py to verify the updated rules produce expected results.
```

### Step 6 — Verification Guidance
After updating the rules, instruct the human to run:
```
python3 scripts/rule-engine-categorize.py \
    --rule-engine scripts/analysis/rule-engine.csv \
    --output-dir scripts/analysis/verification
```
This re-categorizes all tickets with the updated rules. The human can then diff the verification output against the audited CSV to confirm the corrections took effect.

## Rule Evaluation Conventions
- Rules are evaluated by `Priority` (highest first).
- **Meta-rules** (R011, R012, R015, R017 — `Failure Category = Runbook Present = TRUE`) only affect the `Runbook Present` field. They are **excluded** from `Rules Used` and do not determine `Category of Issue` or `Categorization Source`.
- When only meta-rules match, `Categorization Source` remains whatever it would be without them (typically `none`).
- Regex matching is **case-insensitive**.
- `LLM Confidence` mirrors the highest matching category rule's `Confidence` when `Categorization Source = rule`.

## Constraints
- **Never modify** `scripts/trained-data/golden-rules-engine/` — read-only.
- **Never write to `templates/`** — header-only skeletons.
- Only read/write within `scripts/analysis/`.
- Do not re-categorize tickets. Your job is rule maintenance, not categorization.
- When in doubt about a human's intent in `Human Comments`, flag the ambiguity and ask rather than guess.
- Keep rules general enough to match future tickets with similar patterns, but specific enough to avoid false positives. When unsure, err on the side of specificity — it's easier to widen a rule later than to undo false matches.
