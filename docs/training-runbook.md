# Training Runbook (HPC/DO)

## Goal

Predict `Category of Issue` and `Category` for HPC/DO tickets, then improve results through repeated audit and rule updates.

## End-to-End Loop

1. Fetch tickets from Jira:
```bash
uv run python3 scripts/get_tickets.py \
  -a 2026-02-03 2026-02-04 \
  --include-resolved-only \
  --jql-file scripts/jql/hpc_default.jql
```

2. Normalize fetched tickets:
```bash
uv run python3 scripts/normalize_tickets.py --input-dir scripts/tickets-json/
```

3. Categorize with current local rules:
```bash
uv run python3 scripts/rule_engine_categorize.py \
  --rule-engine scripts/trained-data/rule-engine.local.csv \
  --output-dir scripts/analysis
```

4. Human audit:
- Open `scripts/analysis/tickets-categorized.csv`
- Set `Human Audit for Accuracy` to `incorrect` or `needs-review` for rows you want training to process.
- Add `Human Comments` when available.

5. Train / update rules:
```bash
uv run python3 scripts/run_training.py \
  --tickets-categorized scripts/analysis/tickets-categorized.csv \
  --rules-engine-file scripts/trained-data/rule-engine.local.csv \
  --prompt-file prompts/training.md \
  --codex-timeout 120 \
  --codex-batch-size 2 \
  --max-review-rows 200
```

6. Re-run categorization with updated rules:
```bash
uv run python3 scripts/rule_engine_categorize.py \
  --rule-engine scripts/trained-data/rule-engine.local.csv \
  --output-dir scripts/analysis
```

7. Repeat steps 4-6 until stable.

## One-Command Helper

Use the helper script to run steps 1-3 quickly:

```bash
scripts/run_training_loop.sh \
  --start-date 2026-02-10 \
  --end-date 2026-02-12 \
  --jql-file scripts/jql/mi355x_default.jql \
  --rule-engine scripts/trained-data/rule-engine.local.csv \
  --yes
```

Expected checkpoints:
1. `[1/3] Fetching tickets...`
2. `[2/3] Normalizing tickets...`
3. `[3/3] Categorizing with rule engine...`
4. Summary lines with `Rule matched`, `No match`, `Runbook=TRUE`
5. The script prints a ready-to-run command:
```bash
uv run python3 scripts/run_training.py \
  --tickets-categorized scripts/analysis/tickets-categorized.csv \
  --rules-engine-file scripts/trained-data/rule-engine.local.csv \
  --prompt-file prompts/training.md \
  --codex-timeout 120 \
  --codex-batch-size 2 \
  --max-review-rows 200 \
  --yes
```

Then:
1. Audit `scripts/analysis/tickets-categorized.csv`
2. Run the printed `run_training.py` command
3. Re-run categorization
4. Repeat until stable

## ML Training (Optional)

Train the ML classifier from human-labeled data:

```bash
LATEST=$(ls -1 scripts/normalized-tickets | sort | tail -1)
uv run python3 scripts/ml_train.py \
  --training-data scripts/trained-data/ml-training-data.csv \
  --tickets-categorized scripts/analysis/tickets-categorized.csv \
  --tickets-dir "scripts/normalized-tickets/$LATEST" \
  --output-model scripts/trained-data/ml-model/classifier.joblib \
  --output-category-map scripts/trained-data/ml-model/category_map.json \
  --output-report scripts/trained-data/ml-model/training_report.txt \
  --min-samples 20 \
  -y
```

Then re-categorize with ML fallback:

```bash
uv run python3 scripts/rule_engine_categorize.py \
  --tickets-dir "scripts/normalized-tickets/$LATEST" \
  --rule-engine scripts/trained-data/rule-engine.local.csv \
  --ml-model scripts/trained-data/ml-model/classifier.joblib \
  --ml-category-map scripts/trained-data/ml-model/category_map.json \
  --output-dir scripts/analysis \
  -y
```

## Wireframe UI Training Workflow

The wireframe UI (`http://localhost:3000`) provides a "Train STC model" workflow that automates the multi-phase pipeline:

1. **Phase 1:** Fetch → Normalize → Init rules → Initial categorize
2. **Human Audit #1** (skippable via checkbox, default: skipped)
3. **Phase 2:** ML train → ML categorize (rules + ML fallback)
4. **Human Audit #2** (skippable via checkbox, default: skipped)
5. **Phase 3:** LLM rule generation → Final categorize

### Skip-Audit

Both audit pause points default to "skipped" — the pipeline auto-continues without pausing. Uncheck "Skip Human Audit #1" or "Skip Human Audit #2" to enable manual review at those points. When an audit is not skipped, the pipeline pauses and shows an inline CSV editor for reviewing `tickets-categorized.csv`.
