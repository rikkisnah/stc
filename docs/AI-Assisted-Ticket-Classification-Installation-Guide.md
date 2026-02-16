<!-- Code was generated via OCI AI and was reviewed by a human SDE -->
<!-- Tag: #ai-assisted -->

# AI-Assisted Ticket Classification (STC) — Installation Guide

## Scope

This is a pedantic, operational installation and first-run guide for developers who already have repository access. It is written primarily for **macOS**.

## 0) What you will have after setup

- A runnable backend scripts environment (`scripts/` CLI) with Python 3.12+.
- A runnable frontend UX at `http://localhost:3000`.
- Ability to fetch, normalize, categorize, and train on tickets.
- Artifacts written to `scripts/analysis/` and `scripts/analysis/ui-runs/`.

## 1) One-time machine prerequisites (macOS)

### 1.1 Install Homebrew (if missing)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Validate:

```bash
brew --version
```

### 1.2 Install required CLIs/tools

Install all required tools in one pass:

```bash
brew install git python@3.12 node@20 uv
```

Validate one by one:

```bash
python3 --version
uv --version
node --version
npm --version
git --version
```

### 1.3 Optional but recommended: install jq for JSON/debug

```bash
brew install jq
jq --version
```

## 2) Clone or navigate to the repository

If already available locally, `cd` to it:

```bash
cd /path/to/repo/stc
pwd
```

Required:

```bash
ls
```

You should see repository files like `README.md`, `scripts/`, `wireframe-ui/`, `docs/`, `AGENTS.md`.

## 3) Configure Python environment with `uv`

From repository root:

```bash
uv venv .venv
source .venv/bin/activate
python --version
which python
```

Install dependencies:

```bash
uv pip install -r pyproject.toml
```

Quick sanity check:

```bash
uv run python -m pip --version
```

## 4) Configure required environment/token file

STC scripts expect Jira connectivity configuration. Do this before first API call.

Create `env.json` at repository root (same directory as `README.md`):

```bash
cat > env.json <<'EOF_ENV'
{
  "JIRA_URL": "https://your-jira-instance.example.com",
  "JIRA_USER": "your-jira-username",
  "JIRA_TOKEN": "your_api_token_or_auth",
  "JIRA_DEFAULT_PROJECT": "your_project_key"
}
EOF_ENV
```

> Do not commit this file if it contains secrets.

## 5) Run a first backend sanity check

### 5.1 Discover scripts help

```bash
uv run python scripts/get_tickets.py --help
uv run python scripts/normalize_tickets.py --help
uv run python scripts/rule_engine_categorize.py --help
```

Every command should print a usage block and exit with code `0` for `--help`.

### 5.2 Ensure output directories exist

```bash
mkdir -p scripts/tickets-json scripts/normalized-tickets scripts/analysis scripts/logs scripts/trained-data scripts/analysis/ui-runs
ls -la scripts | sed -n '1,120p'
```

## 6) Configure initial rule/training data path (recommended)

For local use, ensure baseline rule file exists:

```bash
ls -l scripts/trained-data/rule-engine.local.csv
ls -l scripts/trained-data/golden-rules-engine/rule-engine.csv
ls -l templates/rule-engine.csv
```

If local file is missing, copy baseline first:

```bash
cp templates/rule-engine.csv scripts/trained-data/rule-engine.local.csv
```

## 6.1 Install frontend dependencies

From repo root:

```bash
cd wireframe-ui
npm ci
cd ..
```

Validate:

```bash
cd wireframe-ui
npm --version
npm run -- --version
cd ..
```

## 7) Start the backend scripts API server (UI runner)

The Next.js UI invokes scripts from a local environment, so activate Python first in same shell.

### 7.1 Open terminal A (backend prep)

```bash
cd /path/to/repo/stc
source .venv/bin/activate
```

### 7.2 Open terminal B (frontend)

```bash
cd /path/to/repo/stc/wireframe-ui
PATH="../.venv/bin:$PATH" npm run dev
```

Expected:

- Terminal B shows Next.js local server starting.
- `http://localhost:3000` is available.

## 8) First UX run (quick verification)

1. Open browser at `http://localhost:3000`.
2. Choose a workflow (for example **Categorize** or **Train STC**).
3. In input fields, provide a small test JQL (or file/paste mode).
4. Keep defaults for first test if available.
5. Click **Run**.
6. Confirm logs stream in real time in the UI.
7. Confirm the run ends with `done` and produces files under:
   - `scripts/analysis/` and/or `scripts/analysis/ui-runs/<run-id>/`

## 9) CLI path for same pipeline (alternative to UI)

Use this if you want to validate the pipeline before opening the browser:

```bash
# Step 1: fetch tickets
uv run python scripts/get_tickets.py -a --jql-file scripts/jql/hpc_default.jql -y

# Step 2: normalize
uv run python scripts/normalize_tickets.py -y

# Step 3: categorize
uv run python scripts/rule_engine_categorize.py \
  --tickets-dir scripts/normalized-tickets/$(ls -1 scripts/normalized-tickets | tail -n 1) \
  --rule-engine scripts/trained-data/golden-rules-engine/rule-engine.csv \
  --output-dir scripts/analysis -y
```

### Verify output

```bash
ls -l scripts/analysis
ls -l scripts/analysis/ui-runs
```

Open generated CSV in your editor and check for columns:
- `Category of Issue`
- `Category`
- `Categorization Source`
- `Human Audit for Accuracy`

## 10) Common first-run issues and fixes (Mac)

### 10.1 `python` resolves to wrong version

```bash
which python
python --version
```

If not 3.12+, run all commands with `python3` or re-activate the uv venv:

```bash
source .venv/bin/activate
```

### 10.2 `zsh: command not found: uv`

Activate Homebrew path and retry:

```bash
export PATH="/opt/homebrew/bin:$PATH"
which uv
```

### 10.3 `npm` fails with permission / legacy lock issues

```bash
cd wireframe-ui
rm -rf node_modules package-lock.json
npm ci
```

### 10.4 Script fails with missing files

Ensure these directories are present:

```bash
mkdir -p scripts/tickets-json scripts/normalized-tickets scripts/analysis scripts/analysis/ui-runs scripts/trained-data scripts/logs
```

### 10.5 UI cannot call backend script or gets path errors

In `wireframe-ui` start command, confirm `.venv` is in `PATH`:

```bash
cd wireframe-ui
echo $PATH
```

Run with:

```bash
PATH="../.venv/bin:$PATH" npm run dev
```

## 11) UI workflow cheat sheet (what each option does)

- `Categorize`: runs fetch/normalize/categorize/summary path.
- `Train STC`: executes phase-gated training with optional audit pauses.
- `Add Rule From Ticket`: builds a new rule from ticket text and persists to rule engine file.
- `Browse Tickets`: reads local raw JSON for inspection.
- `Browse Categorized`: shows existing classification output CSVs.
- `Browse Rules`: inspect `rule-engine*.csv` files.
- `Promote to Golden`: copies approved local rules to golden location.

## 12) Security and local safety checklist

- Never commit credentials: confirm `env.json` is excluded from git commits.
- Keep `scripts/trained-data/golden-rules-engine/` as read-only unless formally promoting.
- Use dated run folders in `scripts/analysis/ui-runs/` for traceability.
- Before every major run, archive previous outputs if required by team policy.

## 13) Minimal completion checklist

- [ ] `brew`, `python3`, `uv`, `node`, `npm` installed
- [ ] `.venv` created and activated
- [ ] `env.json` created with Jira values
- [ ] `scripts/get_tickets.py --help` works
- [ ] `uv run python scripts/normalize_tickets.py --help` works
- [ ] `wireframe-ui` starts with `npm run dev`
- [ ] Browser access to `http://localhost:3000`
- [ ] A sample run writes `scripts/analysis/` output

## 14) Optional next step

After successful install and one successful UX run, use:
- `docs/training-runbook.md` for the full training cadence.
- `docs/human-audit-playbook.md` for audit workflows and field semantics.
