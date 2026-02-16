# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted

# SOP: STC Training & Categorization Cycle

Standard Operating Procedure for running the full STC (Smart Triager Classifier) training and categorization cycle. This covers the end-to-end workflow from raw tickets to a production-ready golden model.

See also: [Training Runbook (CLI reference)](training-runbook.md) | [Human Audit Playbook](human-audit-playbook.md)

## Prerequisites

- `env.json` with Jira credentials at repo root
- `uv sync` completed
- Wireframe UI running (`cd wireframe-ui && PATH="../.venv/bin:$PATH" npm run dev`)

---

## Phase 1: Initial Categorization (Rules + ML Fallback)

**Goal:** Categorize a batch of tickets using existing golden rules and ML model.

1. Open `http://localhost:3000`
2. Click **Categorize tickets**
3. Enter your JQL or ticket IDs
4. Verify fields:
   - Rules engine: `scripts/trained-data/golden-rules-engine/rule-engine.csv`
   - ML model: `scripts/trained-data/golden-ml-model/classifier.joblib`
   - ML category map: `scripts/trained-data/golden-ml-model/category_map.json`
5. Click **OK**
6. Wait for pipeline to complete
7. Review output — note how many are `source="rule"`, `source="ml"`, `source="none"`

---

## Phase 2: Human Audit

**Goal:** Verify the categorization accuracy.

1. Click **View Categorized Tickets** to open the output CSV
2. For each row, edit only two columns:
   - **`Human Audit for Accuracy`**: set to `correct` or `incorrect`
   - **`Human Comments`**: if `incorrect`, explain the right category
3. Pay special attention to:
   - `source="ml"` rows — ML predictions need human verification
   - `source="none"` rows — uncategorized tickets need manual categorization
   - `audit="needs-review"` rows — flagged as low confidence
4. Save the CSV

### Audit Decision Guide

| Situation | Set Audit To | Comment |
|-----------|-------------|---------|
| Category is correct | `correct` | — |
| Category is wrong, you know the right one | `incorrect` | "Should be GPU Failure / GPU" |
| Truly unknown | `incorrect` | "Cannot determine category" |

---

## Phase 3: Train the ML Model

**Goal:** Retrain ML using the audited data so it gets smarter.

1. Click **Train STC model**
2. Use the same JQL/tickets from Phase 1
3. Verify training data path: `scripts/trained-data/ml-training-data.csv`
4. Click **OK**
5. Pipeline runs 3 phases automatically:
   - **Phase 1:** Fetch → Normalize → Initial categorize (rules only)
   - **Phase 2:** Train ML classifier → Re-categorize (rules + ML)
   - **Phase 3:** ML generates new rule proposals → Final categorize
6. Review the training report in the output (CV accuracy, class distribution)

---

## Phase 4: Review Training Output

**Goal:** Verify the trained model and new rules are an improvement.

1. Go to **View Categorized Tickets** → open the latest output
2. Compare to Phase 2 results:
   - Are previously `uncategorized` tickets now categorized?
   - Are the ML predictions reasonable?
   - Did the new rules help?
3. Go to **View Rules Engines** → compare `trained-data` vs `golden`
4. Check for bad rules (overly broad patterns, wrong categories)

---

## Phase 5: Promote to Golden (If Satisfied)

**Goal:** Make the improved rules and ML model the new production baseline.

1. Click **Promote to Golden**
2. **Rules section:**
   - Source: `scripts/trained-data/rule-engine.local.csv`
   - Target: `scripts/trained-data/golden-rules-engine/rule-engine.csv`
   - Click **Load Diff** → review added/changed/removed rules
   - If satisfied → **Promote to Golden** → **Confirm**
3. **ML Model section:**
   - Source: `scripts/trained-data/ml-model`
   - Target: `scripts/trained-data/golden-ml-model`
   - Click **Compare ML Models** → review accuracy metrics
   - If the new model has equal or better accuracy → **Promote ML Model to Golden** → **Confirm**

---

## Phase 6: Regression Check

**Goal:** Confirm the new golden artifacts don't break previously correct categorizations.

1. Re-run **Categorize tickets** with the same JQL from Phase 1
2. Compare output to the audited CSV from Phase 2
3. Every ticket marked `correct` in Phase 2 should still get the same category
4. If regressions found → do NOT promote, iterate from Phase 3

---

## Ongoing Cycle

Repeat this cycle as new ticket types appear:

```
New tickets come in
  → Categorize (rules + golden ML catch most)
  → Human audits the rest
  → Retrain ML (learns new patterns)
  → ML proposes new rules (automates what it learned)
  → Promote to golden (after review)
  → Next batch: fewer uncategorized tickets
```

**Each cycle should reduce the `source="none"` count.** Track this metric over time.

---

## Key Files Reference

| File | Purpose | Who Edits |
|------|---------|-----------|
| `golden-rules-engine/rule-engine.csv` | Production rules | Promote only |
| `golden-ml-model/` | Production ML model | Promote only |
| `rule-engine.local.csv` | Working rules (training output) | Training pipeline |
| `ml-model/` | Working ML model (training output) | Training pipeline |
| `ml-training-data.csv` | Manual human-labeled examples | You (optional, for bootstrapping) |
| `tickets-categorized.csv` | Latest categorization output | Pipeline + human audit |

All paths are relative to `scripts/trained-data/`.

---

## When to Add Manual Labels to `ml-training-data.csv`

Do this when:
- You have a **new category** that no rules cover yet
- The ML model has never seen this category in any audited output
- You want to **bootstrap** a category before the rule→audit→harvest cycle catches up

Format:
```csv
Ticket,Category of Issue,Category,Label Source,Label Date,Notes
HPC-99999,New Category Name,NEW_CAT,human,2026-02-16,First example of this type
```

Add at least 5-10 examples per new category for the ML to learn the pattern.
