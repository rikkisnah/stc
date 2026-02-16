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

# Quick Start — Wireframe UI (Recommended)

The UI is the fastest way to run categorization and training pipelines. It wraps the same CLI scripts with a guided workflow, live logs, and cancel support.

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
| **Train STC model** | Rules-first categorization pipeline with opt-in ML training and rule generation |
| **Add rule from ticket** | Create a rule from a single ticket interactively |
| **Browse tickets** | Explore raw ticket JSON files |
| **Browse categorized** | View categorization output CSVs |
| **Browse rules** | View rule-engine rules (trained-data vs golden) |
| **Promote to Golden** | Promote local rules and ML model to golden (with diff/comparison preview) |

## Train STC Workflow

The Train STC workflow is rules-first by default. ML phases are opt-in via checkboxes.

### Default Run (Rules Only)

1. Click **Train STC model**, enter your JQL or ticket IDs, click **OK**
2. Pipeline runs: fetch → normalize → rules-only categorize → auto-completes
3. Review `tickets-categorized.csv` — rule-matched tickets have `source="rule"`, unmatched have `source="none"`

### Auditing Results

Uncheck **"Skip Human Audit #1"** to pause after categorization. The audit table appears inline:
- Edit `Human Audit for Accuracy` (`correct` / `incorrect`) and `Human Comments`
- For `source="none"` tickets, write the correct category in Human Comments
- Click **Save Changes**, then **Complete Training**

### Enabling ML (When Ready)

Once you have enough audited data (~20+ samples per category), two optional checkboxes appear in the training form:

- **Enable ML Training** — trains a classifier on your audited data, then re-categorizes unmatched tickets using it
- **Enable ML Rule Generation** — uses the trained classifier to propose new rules automatically

Start with rules only. Enable ML training when your audit data is large enough. Enable rule generation once the ML predictions look good.

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

---

# Manual CLI Runbook (Rules + ML)

For advanced use or scripting. ML fallback is automatic when a golden ML model exists.

## Step 1: Fetch Tickets

From repo root, choose one:

JQL file mode:

```bash
uv run python scripts/get_tickets.py -a \
  --jql-file scripts/jql/hpc_default.jql \
  --include-resolved-only \
  2026-02-10 2026-02-11 \
  -y
```

Date range mode:

```bash
uv run python scripts/get_tickets.py -a 2026-02-10 2026-02-11 -y
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

## Step 3: Categorize (Rules Only)

Start with rules-only categorization. Only add the ML flags once you have a trained model for your ticket population.

```bash
uv run python scripts/rule_engine_categorize.py \
  --rule-engine scripts/trained-data/golden-rules-engine/rule-engine.csv \
  --output-dir scripts/analysis \
  -y
```

Output: `scripts/analysis/tickets-categorized.csv`

Tickets matched by rules get `source="rule"`. Unmatched tickets get `source="none"`.

Once you have a golden ML model, add ML fallback so unmatched tickets get a prediction (`source="ml"` if confidence ≥ 0.4):

```bash
uv run python scripts/rule_engine_categorize.py \
  --rule-engine scripts/trained-data/golden-rules-engine/rule-engine.csv \
  --ml-model scripts/trained-data/golden-ml-model/classifier.joblib \
  --ml-category-map scripts/trained-data/golden-ml-model/category_map.json \
  --output-dir scripts/analysis \
  -y
```

## Step 4: Human Audit

Review `scripts/analysis/tickets-categorized.csv`.

Edit only:
- `Human Audit for Accuracy`
- `Human Comments`

For `source="none"` tickets, fill in the correct `Category of Issue` and `Category` in `Human Comments` so they can be used as training data.

Audit values:
- pre-audit pipeline values: `pending-review`, `needs-review`
- post-audit human values: `correct`, `incorrect`

## Step 5: Train ML Model

Once you have enough audited data (~20+ samples per category), train the ML classifier:

```bash
uv run python scripts/ml_train.py \
  --training-data scripts/trained-data/ml-training-data.csv \
  --tickets-categorized scripts/analysis/tickets-categorized.csv \
  --output-model scripts/trained-data/ml-model/classifier.joblib \
  --output-category-map scripts/trained-data/ml-model/category_map.json \
  --output-report scripts/trained-data/ml-model/training_report.txt \
  --min-samples 20 \
  -y
```

Review the training report before proceeding.

## Step 6: Re-Categorize with Rules + New ML Model

```bash
uv run python scripts/rule_engine_categorize.py \
  --rule-engine scripts/trained-data/golden-rules-engine/rule-engine.csv \
  --ml-model scripts/trained-data/ml-model/classifier.joblib \
  --ml-category-map scripts/trained-data/ml-model/category_map.json \
  --output-dir scripts/analysis \
  -y
```

## Step 7: Run Training (ML Rule Generation)

Generate new rules from audited data using the ML engine:

```bash
uv run python scripts/run_training.py \
  --tickets-categorized scripts/analysis/tickets-categorized.csv \
  --rules-engine-file scripts/trained-data/golden-rules-engine/rule-engine.csv \
  --engine ml \
  --ml-model scripts/trained-data/ml-model/classifier.joblib \
  --ml-category-map scripts/trained-data/ml-model/category_map.json \
  -y
```

## Step 8: Re-Categorize with Updated Local Rules

```bash
uv run python scripts/rule_engine_categorize.py \
  --rule-engine scripts/trained-data/rule-engine.local.csv \
  --ml-model scripts/trained-data/ml-model/classifier.joblib \
  --ml-category-map scripts/trained-data/ml-model/category_map.json \
  --output-dir scripts/analysis \
  -y
```

## Step 9: Repeat Audit + Training Until Stable

For subsequent training passes, use:

```bash
--rules-engine-file scripts/trained-data/rule-engine.local.csv
```

## Step 10: Promote to Golden (Manual)

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

# ML Classifier Training (Standalone)

The ML classifier (TF-IDF + SGDClassifier) powers both fallback categorization and ML-based rule generation. See Step 5 in the CLI runbook above for the training command. This section is for standalone retraining outside the full pipeline flow.

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
