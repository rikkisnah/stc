# Purpose

STC - (S)mart (T)riager (C)lassifier is a software that applies LLM with Reinforced Learning to find patterns for DC Ops tickets.

Every categorized ticket carries a confidence score, even when matched purely by deterministic rules. When multiple rules fire, we record the highest rule confidence and surface it in `LLM Confidence`. Rows automatically default to `pending-review`, but fall back to `needs-review` if the computed confidence is below 0.5 so auditors can focus on low-signal items first.

# Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv init
uv add requests
uv add --dev pytest
```

# Pipeline

## The process to use STC

```
Step 1 get tickets
Step 2 normalize tickets
Step 3 run ./run-engine-categorize.py
Step 4 Audit tickets-consolidate.py
Step 4.1 Go through tickets-consolidated.csv (what to look for)
Step 4.2 Add new rules via ./scripts/run-update-rules.sh
Step 5 Run Step 3 again to make sure rules were effect and it worked
```

### Step 4.1 — What to look for in `tickets-consolidated.csv`

- Rows with `LLM Confidence < 0.5` or `Human Audit for Accuracy = needs-review`
- `uncategorized` (or clearly wrong) categories
- Cases where a rule should have matched but `RuleID` is missing/incorrect
- Repeated patterns that should become rules

## Current entrypoints

| Task | Script | Prompt |
|---|---|---|
| Fetch tickets from Jira | `scripts/get_tickets.py` | n/a |
| Normalize tickets | `scripts/normalize_tickets.py` | n/a |
| Train / categorize (batch) | `scripts/run-training.sh` | `prompts/train-to-categorize-tickets-prompt.md` |
| Update rules from feedback | `scripts/run-update-rules.sh` | `prompts/update-rule-engine-prompt.md` |
| Categorize using rules only | `scripts/rule-engine-categorize.py` | n/a |

## Training Phase

```
Step 1  get tickets         ──►  scripts/tickets-json/
Step 2  normalize           ──►  scripts/normalized-tickets/<date>/
Step 3  train (LLM)         ──►  scripts/trained-data/ (rules + categorized CSV)
Step 4  audit (LLM)         ──►  regression-verified snapshots
Step 5  promote golden      ──►  scripts/trained-data/golden-rules-engine/rule-engine.csv
Step 6  categorize all      ──►  scripts/analysis/tickets-categorized.csv
```

### Step 1 — Fetch Tickets

Pull raw JSON from Jira.

```bash
uv run python scripts/get_tickets.py                       # Fetch all tickets
uv run python scripts/get_tickets.py -2d                    # Last 2 days
uv run python scripts/get_tickets.py 2025-01-01             # From start date to now
uv run python scripts/get_tickets.py 2025-01-01 2025-01-31  # Date range
uv run python scripts/get_tickets.py -t DO-2639750          # Single ticket by key
uv run python scripts/get_tickets.py -a --number-of-tickets 5  \
  --output-file scripts/tickets-json/limited-tickets.json      # First 5 tickets to a single file
uv run python scripts/get_tickets.py -a --number-of-tickets 5  \
  --include-unresolved --output-file /tmp/tickets.json         # Override filters + output path
uv run python scripts/get_tickets.py -h                     # Show help
```

Output: `scripts/tickets-json/`

### Step 2 — Normalize Tickets

Transform raw Jira JSON into a compact per-ticket schema for LLM efficiency.

```bash
uv run python scripts/normalize_tickets.py
# Add -y to auto-archive existing outputs, --date to pin directory, or --in-place to overwrite JSONs
uv run python scripts/normalize_tickets.py -y
uv run python scripts/normalize_tickets.py --date 2026-02-11
uv run python scripts/normalize_tickets.py --in-place scripts/tickets-json/DO-*.json
```

Output: `scripts/normalized-tickets/<date>/`

### Step 3 — Train (LLM categorization)

Run the training prompt to categorize 5 tickets per batch against the rule engine, with LLM fallback for unmatched tickets.

```bash
./scripts/run-training.sh
# or use the prompt directly: prompts/train-to-categorize-tickets-prompt.md
```

Working directory: `scripts/trained-data/`

### Step 4 — Audit Regression

After a human audits a training pass (marking tickets correct/incorrect, adjusting rules), re-run categorization and compare field-by-field to the audited snapshot.

```bash
./scripts/run-update-rules.sh
# or use the prompt directly: prompts/update-rule-engine-prompt.md
```

If results match, the rule engine is regression-stable and eligible for golden promotion.

### Step 5 — Promote to Golden

Manually copy the regression-stable `rule-engine.csv` to the golden directory:

```bash
cp scripts/trained-data/rule-engine.csv scripts/trained-data/golden-rules-engine/rule-engine.csv
```

This is a **manual human step** — never automated.

### Step 6 — Categorize All Tickets

Apply the golden rule engine to every normalized ticket. Two options:

**Option A — Rule engine only (fast, no LLM)**
```bash
uv run python scripts/rule-engine-categorize.py
uv run python scripts/rule-engine-categorize.py --tickets-dir scripts/normalized-tickets/2026-02-08
uv run python scripts/rule-engine-categorize.py --rule-engine scripts/trained-data/golden-rules-engine/rule-engine.csv
uv run python scripts/rule-engine-categorize.py --resume  # skip already-categorized tickets
```

**Option B — LLM-assisted (slower, handles uncategorized tickets with LLM reasoning)**
```bash
# (retired) see scripts/archives/ for older LLM batch runners
```

Output: `scripts/analysis/tickets-categorized.csv`

## Human Feedback Loop (post-Step 6)

After reviewing `scripts/analysis/tickets-categorized.csv` and filling in `Human Audit for Accuracy` + `Human Comments`:

```bash
./scripts/run-update-rules.sh
# or use the prompt directly: prompts/update-rule-engine-prompt.md
```

This reads the human feedback and updates `scripts/analysis/rule-engine.csv` — confirming correct rules, fixing incorrect ones, and proposing new rules for uncategorized tickets.

## Overnight Automation

Run training + audit in a loop with optional time limit:

```bash
# (retired) see scripts/archives/ for older overnight runners
```

# Archives

This repo keeps older/retired runners and prompts under:

- `scripts/archives/`
- `prompts/archives/`

These are retained for reference but may not reflect the current pipeline.

# Directory Layout

| Path | Purpose |
|---|---|
| `scripts/tickets-json/` | Raw Jira JSON (Step 1 output) |
| `scripts/normalized-tickets/<date>/` | Normalized per-ticket JSON (Step 2 output) |
| `scripts/trained-data/` | Working directory for training sessions (Steps 3-4) |
| `scripts/trained-data/golden-rules-engine/` | **Read-only.** Production rule engine (Step 5) |
| `scripts/analysis/` | Output from full categorization runs (Step 6) |
| `templates/` | CSV header-only skeletons. **Never write working data here.** |
| `prompts/` | LLM prompt files |

# LLM Prompts

| Prompt | Purpose | Runner Script |
|---|---|---|
| `prompts/train-to-categorize-tickets-prompt.md` | Few-shot training: rule-match + LLM fallback, 5 tickets/batch | `scripts/run-training.sh` |
| `prompts/update-rule-engine-prompt.md` | Update/extend the rule engine from feedback | `scripts/run-update-rules.sh` |

# Running Tests

```bash
uv run pytest scripts/test_get_tickets.py -v
```

# Glossary

## LLM Confidence

A 0.0–1.0 score indicating how reliable a ticket's categorization is. The value depends on `Categorization Source`:

| Source | How LLM Confidence is set |
|---|---|
| `rule` | The highest `Confidence` value among all matching rules. A rule with `Confidence = 1.0` means a human has confirmed it (`Created By = human-confirmed`); `0.7` is a typical LLM-suggested rule. |
| `llm` | The model's self-reported confidence in its reasoning when no rule matched. |

Tickets with `LLM Confidence < 0.5` are automatically flagged as `needs-review` so auditors can prioritize low-signal items. All other tickets default to `pending-review`.

## Human Audit for Accuracy

Tracks the review state of each categorized ticket. Set automatically by the pipeline and updated manually by a human auditor.

| Value | Set by | Meaning |
|---|---|---|
| `pending-review` | Pipeline | A rule matched with confidence >= 0.5. Categorization is likely correct but has not been verified by a human yet. |
| `needs-review` | Pipeline | Either no rules matched (category = `uncategorized`) or confidence was below 0.5. These tickets need priority human attention because the system is uncertain. |
| `correct` | Human | Auditor confirmed the categorization is accurate. |
| `incorrect` | Human | Auditor determined the categorization is wrong. Should include details in `Human Comments`. |

# FAQ

## What is the Jira Query used to query the tickets?

```
(labels = GPU_V6_E6-IS_MI355X_S.01 OR "Rack Type" = GPU_MI355X_E6_R.01) AND status != "Pending Part(s)" AND (("Region / Domain" IN (aga.ad1, "AGA5 (AD)") OR "Region Affected" = AGA OR "Canonical AD" = aga.ad1 OR Building = aga5) AND ("Rack Type" IN (GPU_MI355X_E6_R.02, GPU_MI355X_E6_R.01) OR labels IN (GPU_V6_E6-IS_MI355X_S.02, GPU_V6_E6-IS_MI355X_S.01, AGA-CPV)) AND resolution = Unresolved AND summary !~ "Master") AND project = "DC Ops" AND "Component / Item" NOT IN cascadeOption(10046, 10064)
```
