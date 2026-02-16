# Purpose

STC ((S)mart (T)riager (C)lassifier) predicts two ticket outputs for HPC and DO workloads:
- `Category of Issue`
- `Category`

The default workflow is rule-based categorization with ML fallback for unmatched tickets. Rule updates can be generated via a local ML classifier (preferred — fast, offline) or optionally via an LLM/Codex provider (slower, requires API access).

## Core Principles

- Keep all runtime artifacts under `scripts/`.
- Treat `scripts/trained-data/golden-rules-engine/rule-engine.csv` as production/audited rules.
- Treat `scripts/trained-data/golden-ml-model/` as the production/audited ML model.
- Human audit is required before promoting new rules or ML models to golden.
- ML-based rule generation is the preferred engine (`--engine ml`) — fast and offline.
- LLM/Codex-based rule generation is optional (`--engine codex`) — slower, requires API access and token setup.

# Repository Layout

| Path | Purpose |
|---|---|
| `scripts/get_tickets.py` | Pull Jira tickets into JSON files |
| `scripts/normalize_tickets.py` | Normalize raw Jira JSON |
| `scripts/rule_engine_categorize.py` | Categorize tickets using rules (optional ML fallback) |
| `scripts/run_training.py` | Generate/update rules from audited rows (ML preferred, LLM optional) |
| `scripts/create_summary.py` | Produce category summary CSV + JQL |
| `scripts/tickets-json/` | Raw ticket JSON output |
| `scripts/normalized-tickets/<date>/` | Normalized ticket JSON output |
| `scripts/analysis/` | Categorization and analysis outputs |
| `scripts/trained-data/` | Working rule-engine and model/training artifacts |
| `scripts/trained-data/golden-rules-engine/` | Audited production rules |
| `scripts/trained-data/golden-ml-model/` | Audited production ML model |
| `templates/` | Header/template CSVs (do not write live outputs here) |
| `scripts/ml_train.py` | Train ML classifier (TF-IDF + SGD) |
| `scripts/ml_classifier.py` | ML classification module |
| `scripts/create_rule_from_ticket.py` | Create rule from single ticket |
| `scripts/csv_jql_transform.py` | CSV metadata augmentation |
| `scripts/run_training_loop.sh` | One-command helper (fetch→normalize→categorize) |
| `scripts/trained-data/ml-model/` | Trained ML classifier artifacts |
| `wireframe-ui/` | Local Next.js wireframe UI |
| `docs/` | Design docs, runbooks, and reference materials |
| `docs/AI-Assisted-Ticket-Classification-design-doc.md` | Detailed design document |
| `docs/archives/` | Archived/historical documentation |
| `SKILLS/` | TDD role definitions (architect, tester, coder, reviewer) |

# Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+ (for `wireframe-ui`)
- Jira token in repo-root `env.json`

Example `env.json`:

```json
{
  "JIRA_URL": "https://your-jira-instance.example.com",
  "JIRA_USER": "your-user",
  "JIRA_TOKEN": "YOUR_JIRA_TOKEN",
  "JIRA_DEFAULT_PROJECT": "PROJECT_KEY"
}
```

# Setup

From repo root:

```bash
uv sync
```

# Backend Runbook (Rules + ML)

This is the recommended flow. ML fallback is automatic when a golden ML model exists.

## Step 1: Fetch Tickets

From repo root, choose one:

JQL file mode:

```bash
uv run python scripts/get_tickets.py -a \
  --jql-file scripts/jql/hpc_default.jql \
  --include-unresolved \
  -y
```

Date range mode:

```bash
uv run python scripts/get_tickets.py -a 2026-02-14 2026-02-15 -y
```

Single ticket mode:

```bash
uv run python scripts/get_tickets.py -t DO-2639750
```

Output: `scripts/tickets-json/`

## Step 2: Normalize

```bash
uv run python scripts/normalize_tickets.py -y
```

Output: `scripts/normalized-tickets/<date>/`

## Step 3: Categorize (Rules + ML Fallback)

```bash
LATEST=$(ls -1 scripts/normalized-tickets | sort | tail -1)
uv run python scripts/rule_engine_categorize.py \
  --tickets-dir "scripts/normalized-tickets/$LATEST" \
  --rule-engine scripts/trained-data/golden-rules-engine/rule-engine.csv \
  --ml-model scripts/trained-data/golden-ml-model/classifier.joblib \
  --ml-category-map scripts/trained-data/golden-ml-model/category_map.json \
  --output-dir scripts/analysis \
  -y
```

Output: `scripts/analysis/tickets-categorized.csv`

Tickets matched by rules get `source="rule"`. Unmatched tickets fall back to the ML model (`source="ml"` if confidence ≥ 0.4, otherwise `source="none"`). Omit the `--ml-model` flags for rules-only categorization.

## Step 4: Human Audit

Review `scripts/analysis/tickets-categorized.csv`.

Edit only:
- `Human Audit for Accuracy`
- `Human Comments`

Audit values:
- pre-audit pipeline values: `pending-review`, `needs-review`
- post-audit human values: `correct`, `incorrect`

## Step 5: Run Training (ML Preferred)

**ML engine (recommended — fast, offline):**

```bash
uv run python scripts/run_training.py \
  --tickets-categorized scripts/analysis/tickets-categorized.csv \
  --rules-engine-file scripts/trained-data/golden-rules-engine/rule-engine.csv \
  --engine ml \
  --ml-model scripts/trained-data/golden-ml-model/classifier.joblib \
  --ml-category-map scripts/trained-data/golden-ml-model/category_map.json \
  -y
```

**LLM/Codex engine (optional — slower, requires API access):**

```bash
uv run python scripts/run_training.py \
  --tickets-categorized scripts/analysis/tickets-categorized.csv \
  --rules-engine-file scripts/trained-data/golden-rules-engine/rule-engine.csv \
  --prompt-file prompts/training.md \
  --engine <provider> \
  --codex-timeout 180 \
  --codex-batch-size 2 \
  -y
```

This writes updates to `scripts/trained-data/rule-engine.local.csv`.

## Step 6: Re-Categorize with Updated Local Rules

```bash
uv run python scripts/rule_engine_categorize.py \
  --tickets-dir "scripts/normalized-tickets/$LATEST" \
  --rule-engine scripts/trained-data/rule-engine.local.csv \
  --ml-model scripts/trained-data/golden-ml-model/classifier.joblib \
  --ml-category-map scripts/trained-data/golden-ml-model/category_map.json \
  --output-dir scripts/analysis \
  -y
```

## Step 7: Repeat Audit + Training Until Stable

For subsequent training passes, use:

```bash
--rules-engine-file scripts/trained-data/rule-engine.local.csv
```

## Step 8: Promote to Golden (Manual)

Only after human-audited regression stability:

```bash
# Promote rules
cp scripts/trained-data/rule-engine.local.csv \
  scripts/trained-data/golden-rules-engine/rule-engine.csv

# Promote ML model
cp scripts/trained-data/ml-model/classifier.joblib \
  scripts/trained-data/golden-ml-model/classifier.joblib
cp scripts/trained-data/ml-model/category_map.json \
  scripts/trained-data/golden-ml-model/category_map.json
cp scripts/trained-data/ml-model/training_report.txt \
  scripts/trained-data/golden-ml-model/training_report.txt
```

Both promotions are intentionally manual. The wireframe UI provides a "Promote to Golden" workflow with diff preview for rules and side-by-side comparison for ML models.

# One-Command Helper

`scripts/run_training_loop.sh` runs fetch -> normalize -> categorize, then prints the follow-up `run_training.py` command.

Provider example:

```bash
scripts/run_training_loop.sh \
  --start-date 2026-02-10 \
  --end-date 2026-02-12 \
  --jql-file scripts/jql/hpc_default.jql \
  --rule-engine scripts/trained-data/rule-engine.local.csv \
  --engine <provider> \
  --yes
```

# ML Classifier Training

The ML classifier (TF-IDF + SGDClassifier) powers both fallback categorization and ML-based rule generation. Retrain it when you have new audited data:

```bash
uv run python scripts/ml_train.py \
  --training-data scripts/trained-data/ml-training-data.csv \
  --tickets-categorized scripts/analysis/tickets-categorized.csv \
  --tickets-dir "scripts/normalized-tickets/$LATEST" \
  --output-model scripts/trained-data/ml-model/classifier.joblib \
  --output-category-map scripts/trained-data/ml-model/category_map.json \
  --output-report scripts/trained-data/ml-model/training_report.txt \
  --min-samples 20 \
  -y
```

After reviewing the training report, promote to golden:

```bash
cp scripts/trained-data/ml-model/* scripts/trained-data/golden-ml-model/
```

# Optional: LLM/Codex Rule Generation (Slow)

LLM-based rule generation is available but **not recommended** for routine use — it requires API access, token setup, and is significantly slower than the ML engine.

## Hybrid Training (LLM + ML)

```bash
uv run python scripts/run_training.py \
  --tickets-categorized scripts/analysis/tickets-categorized.csv \
  --rules-engine-file scripts/trained-data/rule-engine.local.csv \
  --prompt-file prompts/training.md \
  --engine <provider>+ml \
  --ml-model scripts/trained-data/ml-model/classifier.joblib \
  --ml-category-map scripts/trained-data/ml-model/category_map.json \
  -y
```

For rules-only (no ML) with LLM, use `--engine <provider>` without ML flags.

# Wireframe UI

Run locally:

```bash
cd wireframe-ui
npm ci
PATH="../.venv/bin:$PATH" npm run dev
```

Open `http://localhost:3000`.

## Available Workflows

| Workflow | Description |
|----------|-------------|
| **Categorize** | Run JQL → categorization pipeline (get_tickets → normalize → categorize with ML fallback → summary) |
| **Train STC model** | Multi-phase training with ML classifier and ML-based rule generation |
| **Add rule from ticket** | Create a rule from a single ticket interactively |
| **Browse tickets** | Explore raw ticket JSON files |
| **Browse categorized** | View categorization output CSVs |
| **Browse rules** | View rule-engine rules (trained-data vs golden) |
| **Promote to Golden** | Promote local rules and ML model to golden (with diff/comparison preview) |

## Train STC Workflow

The Train STC workflow runs a multi-phase pipeline:

1. **Phase 1:** Fetch tickets → Normalize → Init local rules → Initial categorize
2. **Human Audit #1** (skippable, default: skipped)
3. **Phase 2:** ML train → ML categorize (rules + ML fallback)
4. **Human Audit #2** (skippable, default: skipped)
5. **Phase 3:** ML rule generation → Final categorize (LLM optional via `--engine codex`)

Both audit pause points are configurable via checkboxes in the UI. When skipped (default), the pipeline auto-continues to the next phase without pausing.

Outputs are written under `scripts/analysis/ui-runs/<run-id>/`.

## UI Quality Gate (Required)

For any change under `wireframe-ui/`, run this before handoff:

```bash
make ui-verify
```

`make ui-verify` is a blocking gate and runs:
- `npm test` (unit tests)
- `npx tsc --noEmit` (typecheck)
- clean Next build (`rm -rf wireframe-ui/.next` + `npm run build`)
- runtime smoke against built app (`make UI_SMOKE_MODE=start ui-runtime-smoke`) to catch runtime/chunk module errors such as `Cannot find module`
- Playwright E2E (`npm run test:e2e`)

If this gate fails, the UI change is not complete.

# Tests

Backend:

```bash
uv run pytest --cov=scripts --cov-report=term-missing -q scripts/tests
```

Wireframe unit tests:

```bash
cd wireframe-ui
npm test
```

Wireframe E2E:

```bash
make ui-e2e
```

Wireframe fast local check (iteration loop):

```bash
make ui-quick
```

Wireframe full gate (required for `wireframe-ui/` changes):

```bash
make ui-verify
```

# Make Targets

Show available commands:

```bash
make help
```

Notable targets:
- `test`
- `run-training`
- `run-training-inline`
- `ui-e2e-setup`
- `ui-quick`
- `ui-clean-cache`
- `ui-runtime-smoke`
- `ui-e2e`
- `ui-verify`
- `test-ml_classifier`
- `test-ml_train`
- `ml-train`
- `ml-categorize`

# Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide (Mac-first)](docs/AI-Assisted-Ticket-Classification-Installation-Guide.md) | Pedantic install and first-UX-run guide |
| [Detailed Design](docs/AI-Assisted-Ticket-Classification-design-doc.md) | Comprehensive detailed design document |
| [HLD (prior art)](docs/pdfs_docs/AI-Assisted-Ticket-Classification-HLD.docx) | Original high-level design |
| [Training Runbook](docs/training-runbook.md) | Step-by-step training workflow |
| [Human Audit Playbook](docs/human-audit-playbook.md) | Row-level audit procedures |
| [Data Schemas](templates/data-schemes.md) | CSV schema definitions |
| [Optional LLM CLI setup](docs/installing-codex.md) | Optional LLM CLI setup (Codex/Oracle internal context) |
