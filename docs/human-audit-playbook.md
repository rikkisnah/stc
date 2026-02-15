# Human Audit Playbook

## Goal

Use human review feedback from `tickets-categorized.csv` to improve rule quality in the next rule update pass.

## Columns Humans Edit

Edit only:
- `Human Audit for Accuracy`
- `Human Comments`

Do not edit:
- `Human Audit Guidance` (system reminder)

## Allowed Values

`Human Audit for Accuracy` values:
- `pending-review` (pipeline pre-audit)
- `needs-review` (pipeline pre-audit)
- `correct` (human post-audit)
- `incorrect` (human post-audit)

During audit, humans should set final values to:
- `correct`
- `incorrect`

## Row-Level Procedure

1. Open `Ticket URL`.
2. Validate whether `Category of Issue`, `Category`, and `Rules Used` are correct.
3. Set `Human Audit for Accuracy = correct` if classification is acceptable.
4. Set `Human Audit for Accuracy = incorrect` if classification is wrong or too vague.
5. When `incorrect`, write a concrete correction in `Human Comments`:
- expected category
- short reason
- rule hint (keywords, field to match, false positive/negative)

## Example: Needs-Review Row

Input row pattern:
- `Category of Issue = uncategorized`
- `Categorization Source = none`
- `Human Audit for Accuracy = needs-review`

Typical action:
- Set `Human Audit for Accuracy = incorrect`
- Set `Human Comments` similar to:
`Expected category is CPV Job Timeout. Summary contains CPV Job Timeout and sunvts_burnin. Add summary rule for this pattern.`

Exception:
- If truly unknown after review, set `Human Audit for Accuracy = correct` and note:
`New pattern. Uncategorized is acceptable for now.`

## After Human Edits

1. Run rule update from feedback:
```bash
./scripts/run-update-rules.sh
```
2. Re-run categorization:
```bash
uv run python scripts/rule-engine-categorize.py \
  --tickets-dir scripts/normalized-tickets/<date> \
  --rule-engine scripts/trained-data/golden-rules-engine/rule-engine.csv \
  --output-dir scripts/analysis
```
3. Re-audit remaining `needs-review` or wrong rows and repeat until stable.
