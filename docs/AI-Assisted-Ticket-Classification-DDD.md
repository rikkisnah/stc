<!-- Code was generated via OCI AI and was reviewed by a human SDE -->
<!-- Tag: #ai-assisted -->

# AI-Assisted Ticket Classification — Detailed Design Document (DDD)

## 1. Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0 Draft |
| **Author** | Rik Kisnah |
| **Date** | February 2026 |
| **Classification** | Internal |
| **System Name** | Smart Triager Classifier (STC) |
| **Division** | DC Ops \| Oracle Cloud Infrastructure |
| **Team** | DC Ops - Sudha's Team |
| **Target Region** | AGA (MI355X GPU Racks) |
| **References** | AI-Assisted-Ticket-Classification-HLD.docx (prior art, in `docs/pdfs_docs/`) |

---

## 2. Executive Summary

STC is an LLM-bootstrapped pipeline that classifies DC Ops GPU failure tickets into structured categories. It combines:

- **Deterministic rule-based matching** (primary path)
- **ML classifier fallback** (TF-IDF + SGDClassifier)
- **LLM-assisted rule generation** (Codex)
- **Human-in-the-loop audit** with configurable skip

**Key distinction:** STC is NOT a RAG or pure LLM system. The LLM bootstraps a deterministic rule engine that progressively operates independently. This enables TPMs and managers to categorize approximately 100 JIRA tickets in less than 10 minutes.

The system includes a wireframe UI (Next.js) for local pipeline execution and a multi-phase training workflow with configurable audit pause points.

---

## 3. Problem Statement

| Problem | Impact |
|---------|--------|
| **Manual Triage Bottleneck** | Engineers spend excessive time manually categorizing GPU failure tickets |
| **Inconsistent Categorization** | Different team members apply different categories to similar issues |
| **Delayed Hotspot Detection** | Patterns in failures are not identified quickly enough for proactive action |
| **No Runbook Visibility** | Tickets with existing runbook resolutions are not flagged consistently |
| **Executive Reporting Gap** | Leadership lacks structured, timely summaries of failure categories and trends |

---

## 4. Solution Architecture

### Two-Stage Pipeline

- **Stage 1: Data Pipeline** — JIRA ingestion followed by normalization
- **Stage 2: Classification & Audit** — Rule engine + ML fallback + LLM, then human audit, golden rules promotion, and executive report generation

### Data Flow

```
JIRA API
  → Raw JSON
    → Normalized JSON
      → Rule Engine (+ ML fallback)
        → Categorized CSV
          → Human Audit
            → Rule Updates (LLM)
              → Golden Rules
                → Executive Report
```

The wireframe UI provides a web interface for all pipeline stages with real-time log streaming.

---

## 5. Pipeline Stages

The training pipeline operates in **3 phases** with **2 configurable audit pause points**:

| Phase | Step | Name | Script | Output |
|-------|------|------|--------|--------|
| 1 | 1 | Fetch Tickets | `get_tickets.py` | `scripts/tickets-json/` |
| 1 | 2 | Normalize | `normalize_tickets.py` | `scripts/normalized-tickets/<date>/` |
| 1 | 3 | Init Local Rules | (copy golden to local) | `rule-engine.local.csv` |
| 1 | 4 | Initial Categorize | `rule_engine_categorize.py` | `tickets-categorized.csv` |
| — | 5 | Human Audit #1 | (manual/skippable) | Audited CSV |
| 2 | 6 | ML Train | `ml_train.py` | `classifier.joblib`, `category_map.json` |
| 2 | 7 | ML Categorize | `rule_engine_categorize.py` (`--ml-model`) | Updated CSV with ML fallback |
| — | 8 | Human Audit #2 | (manual/skippable) | Audited CSV |
| 3 | 9 | LLM Rule Generation | `run_training.py` | Updated `rule-engine.local.csv` |
| 3 | 10 | Final Categorize | `rule_engine_categorize.py` | Final `tickets-categorized.csv` |

**Skip-audit:** Both audit points default to "skipped" in the wireframe UI. When skipped, the pipeline auto-continues to the next phase. Users can uncheck to enable manual audit pauses.

---

## 6. Core Components

### 6.1 Rule Engine

A CSV-based pattern store evaluated in priority order.

- Regex patterns matched case-insensitively against ticket fields
- Fields: `summary`, `description`, `labels`, `comments` (combinable with `+`)
- When multiple rules match, the highest-priority match wins
- Confidence is propagated as the maximum across all matching rules

**Rule CSV Columns:**

| Column | Description |
|--------|-------------|
| Project Key | JIRA project identifier |
| RuleID | Unique rule identifier |
| Rule Pattern | Regex pattern |
| Match Field | Ticket field(s) to match against |
| Failure Category | Category of Issue value |
| Category | Sub-category value |
| Priority | Rule evaluation order (lower = higher priority) |
| Confidence | Match confidence (0.0-1.0) |
| Created By | Origin: `llm-suggested`, `human-confirmed`, etc. |
| Hit Count | Number of times rule has matched |

**Rule Lifecycle:**

1. LLM proposes pattern (Confidence: 0.7)
2. Human reviews during audit
3. **Confirmed** — confidence bumped to 0.95-1.0; Created By set to `human-confirmed`
4. **Rejected** — pattern adjusted or removed
5. Promoted to Golden Rule Engine (read-only production copy)

### 6.2 ML Classifier

| Parameter | Value |
|-----------|-------|
| Algorithm | TF-IDF vectorizer + SGDClassifier (sklearn) |
| Confidence threshold | 0.4 (below this yields uncategorized) |
| Minimum training samples | 20 |
| Feature text | summary + description + labels + comments |
| Role | Fallback when no rule matches |
| Artifacts | `classifier.joblib`, `category_map.json`, `training_report.txt` |

Training data is harvested from rule-matched and human-audited tickets.

### 6.3 LLM Training Engine (`run_training.py`)

- **Engines:** `codex` (LLM only), `ml` (fast), `codex+ml` (hybrid)
- **Input:** `tickets-categorized.csv` with human audit feedback
- **Processes:** incorrect and needs-review rows
- **Output:** updated `rule-engine.local.csv` with new or modified rules
- **Prompt template:** `prompts/training.md`
- **Processing:** batch-based with configurable timeout and batch size

### 6.4 Wireframe UI

| Aspect | Detail |
|--------|--------|
| Framework | Next.js 15, React 19, TypeScript |
| Workflows | categorize, train-stc, add-rule, browse-tickets, browse-categorized, browse-rules, promote-to-golden |
| Streaming | Real-time log streaming via NDJSON over HTTP |
| Cancellation | SIGTERM to child processes |
| Artifacts | Stored in `scripts/analysis/ui-runs/<run-id>/` |

---

## 7. Data Schemas

Reference: `templates/data-schemes.md`

### rule-engine.csv

```
Project Key, RuleID, Rule Pattern, Match Field, Failure Category, Category, Priority, Confidence, Created By, Hit Count
```

### tickets-categorized.csv

```
Project Key, Ticket, Ticket URL, Ticket Description, Status, Created, Age, Runbook Present, Category of Issue, Category, Rules Used, Categorization Source, LLM Confidence, Human Audit for Accuracy, Human Audit Guidance, Human Comments
```

### ml-training-data.csv

```
Ticket, Category of Issue, Category, Label Source, Label Date, Notes
```

---

## 8. Confidence Model

| Source | Mechanism | Details |
|--------|-----------|---------|
| **Rule confidence** | Maximum confidence among matching rules | 1.0 = human-confirmed, 0.7 = LLM-suggested |
| **ML confidence** | Model's predicted probability for top class | Threshold: 0.4 |
| **LLM confidence** | Self-reported based on reasoning quality | Varies per response |

**Triage threshold:**

- `LLM Confidence < 0.5` — auto-flagged as `needs-review`
- `LLM Confidence >= 0.5` — set to `pending-review`

---

## 9. Human-in-the-Loop Design

**Principle:** Humans gate every rule promotion; the LLM is a pattern discovery engine only.

### Feedback Loop

```
LLM Proposes → Human Reviews → Rules Updated → Regression Test → Golden Promotion → Production Use
```

### Audit Verdicts

| Verdict | Action |
|---------|--------|
| `correct` | Bump rule confidence toward 1.0, set Created By = `human-confirmed` |
| `incorrect` | Parse Human Comments for corrections, adjust rules |
| `needs-review` | Skip during training, leave for deeper review |

**Editable columns during audit:** `Human Audit for Accuracy`, `Human Comments` only.

**Never edit:** `Human Audit Guidance` (system-generated).

### Skip-Audit Feature

In the wireframe UI, both audit pause points can be toggled via checkboxes ("Skip Human Audit #1", "Skip Human Audit #2"). Both default to skipped. When enabled, the pipeline auto-continues without pausing.

---

## 10. Runbook Detection

Meta-rules that set `Runbook Present = TRUE` without influencing category:

| Rule | Pattern |
|------|---------|
| R011 | "TRS prescription" or "Resolving for TRS" in comments |
| R012 | `TRS_PRESCRIPTIVE_TICKET` label |
| R015 | "Prescriptive Action" in title |
| R017 | "RHS Hardware Update/Action Plan" in comments |
| — | "known bug" in text |

---

## 11. Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Data Source | JIRA REST API | Ticket extraction with JQL filters |
| Ingestion Scripts | Python 3.12+ (requests, argparse) | Fetch, normalize, compact data |
| Rule Engine | CSV + Python regex | Deterministic pattern matching |
| ML Classifier | scikit-learn (TF-IDF + SGD) | Fallback classification |
| LLM (Training) | Claude (Anthropic) / Codex | Pattern discovery, rule generation |
| LLM Interface | Claude Code CLI / Codex CLI | Session-based training |
| Wireframe UI | Next.js 15, React 19, TypeScript | Local pipeline execution |
| UI Testing | Jest (unit), Playwright (E2E) | Frontend quality gate |
| Backend Testing | pytest (100% coverage) | Python script validation |
| Storage | File-based (JSON + CSV) | Normalized tickets and rules |
| Version Control | Git with snapshot archival | Pass-suffixed CSVs for audit trail |
| Package Manager | uv (Python), npm (Node.js) | Dependency management |

---

## 12. Directory Structure

```
stc/
├── README.md
├── CLAUDE.md / AGENTS.md        # TDD governance (identical)
├── MEMORY.md                    # Project decisions and constraints
├── TASKS.md                     # Active work tracking
├── Makefile                     # Build commands
├── pyproject.toml               # Python config
├── env.json                     # Jira token (gitignored values)
├── scripts/
│   ├── get_tickets.py           # Jira ticket fetcher
│   ├── normalize_tickets.py     # Ticket normalization
│   ├── rule_engine_categorize.py # Rule-based + ML categorization
│   ├── run_training.py          # LLM rule generation
│   ├── ml_train.py              # ML classifier training
│   ├── ml_classifier.py         # ML classification module
│   ├── create_summary.py        # Category summary CSV
│   ├── create_rule_from_ticket.py # Interactive rule creation
│   ├── csv_jql_transform.py     # CSV metadata augmentation
│   ├── run_training_loop.sh     # One-command helper
│   ├── sync_agents_claude.py    # AGENTS/CLAUDE sync
│   ├── jql/                     # JQL query templates
│   ├── tickets-json/            # Raw Jira JSON (Step 1)
│   ├── normalized-tickets/      # Normalized JSON (Step 2)
│   ├── trained-data/            # Working rules + ML model
│   │   ├── rule-engine.local.csv
│   │   ├── ml-training-data.csv
│   │   ├── ml-model/            # classifier.joblib, category_map.json
│   │   └── golden-rules-engine/ # READ-ONLY production rules
│   ├── analysis/                # Categorization outputs
│   │   └── ui-runs/             # Wireframe UI run artifacts
│   ├── logs/                    # Execution logs
│   └── tests/                   # pytest suite (100% coverage)
├── wireframe-ui/
│   ├── app/
│   │   ├── page.tsx             # Main SPA
│   │   └── api/                 # Next.js API routes
│   │       ├── run-jql/         # Categorization pipeline
│   │       ├── train-stc/       # Multi-phase training
│   │       ├── add-rule-from-ticket/ # Rule creation
│   │       ├── list-files/      # Directory browser
│   │       ├── open-file/       # File reader
│   │       ├── save-file/       # File writer
│   │       └── tickets-json/    # Ticket browser
│   └── __tests__/               # Jest unit tests
├── templates/                   # Header-only CSV templates
│   ├── rule-engine.csv
│   ├── tickets-categorized.csv
│   ├── ml-training-data.csv
│   └── data-schemes.md          # Schema documentation
├── prompts/
│   └── training.md              # LLM prompt for rule generation
├── docs/
│   ├── AI-Assisted-Ticket-Classification-DDD.md  # This document
│   ├── human-audit-playbook.md  # Row-level audit procedures
│   ├── training-runbook.md      # Step-by-step training guide
│   ├── installing-codex.md      # Codex CLI setup
│   ├── mi300x_fault_dictionary.md # Hardware fault reference
│   ├── help_chs_aga_mi355x.md  # MI355X domain context
│   ├── pdfs_docs/               # Original design documents
│   │   └── AI-Assisted-Ticket-Classification-HLD.docx
│   └── archives/                # Historical/outdated docs
│       ├── executive-email-ask.md
│       └── labeling_automation-tyler-org.md
└── SKILLS/                      # TDD role definitions
    ├── architect/
    ├── tester/
    ├── coder/
    └── reviewer/
```

---

## 13. API Reference (Wireframe UI)

### POST /api/run-jql

Executes the categorization pipeline (get_tickets, normalize, categorize, summary).

**Request:**

```json
{
  "inputMode": "jql|file|paste",
  "jql": "string",
  "resolutionMode": "string",
  "ticketsFile": "string",
  "ticketsText": "string"
}
```

**Response:** NDJSON stream with events: `pipeline-start`, `command-start`, `stdout`, `stderr`, `command-end`, `done`, `error`, `canceled`

### POST /api/train-stc

Multi-phase training pipeline with audit pause points.

**Request (Phase 1):**

```json
{
  "phase": 1,
  "inputMode": "jql|file|paste",
  "jql": "string",
  "resolutionMode": "string",
  "ticketsFile": "string",
  "ticketsText": "string",
  "trainingData": "string",
  "minSamples": 20,
  "maxReviewRows": 50
}
```

**Request (Phase 2 or 3):**

```json
{
  "phase": 2,
  "runId": "string"
}
```

**Response:** NDJSON stream with events including `paused` (audit pause) and `done`

### POST /api/add-rule-from-ticket

Creates a rule from a single ticket.

**Request:**

```json
{
  "ticketKey": "string",
  "reason": "string",
  "failureCategory": "string",
  "category": "string",
  "matchField": "string",
  "rulePattern": "string",
  "ticketJsonDir": "string",
  "normalizedRoot": "string",
  "rulesEngine": "string",
  "matchFieldDefault": "string",
  "priority": 100,
  "confidence": 0.7,
  "createdBy": "string",
  "hitCount": 0
}
```

### GET /api/list-files?dir=...&extensions=...

Lists files in allowed directories.

### GET /api/open-file?path=...

Reads file content from allowed paths.

### POST /api/save-file

Writes file content.

**Request:**

```json
{
  "path": "string",
  "content": "string"
}
```

### GET /api/tickets-json

Lists tickets from `scripts/tickets-json/`.

---

## 14. Design Principles

1. **Human-Gated Rule Promotion** — LLM discovers, humans approve
2. **Confidence-Driven Triage** — automatic flagging below threshold
3. **Dual-Source Tracking** — rule vs ML vs LLM vs none provenance
4. **Meta-Rule Separation** — runbook detection isolated from categorization
5. **Snapshot Archival** — pass-numbered CSVs for regression and rollback
6. **Deterministic Reproducibility** — same rules + same tickets = same output
7. **Progressive Autonomy** — reduce LLM dependence as rules mature
8. **Frontend-First UX** — wireframe UI works independently of backend services
9. **Configurable Audit** — skip-audit defaults allow fast iteration; enable for careful review
10. **File-Based Simplicity** — CSV/JSON storage avoids database dependencies

---

## 15. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Categorization Time | <10 minutes for 100 tickets | End-to-end pipeline time |
| Rule Engine Coverage | >80% tickets matched by rules | % with Source = rule |
| Classification Accuracy | >90% correct on human audit | % audited tickets marked correct |
| Runbook Detection Rate | 100% of known runbook tickets | False negative rate |
| Rule Stability | Zero regression failures | Audit regression pass rate |
| ML Fallback Coverage | >50% of unmatched tickets | % of Source=ml among Source!=rule |

---

## 16. Testing Strategy

### Python Backend (100% line coverage required)

- **Framework:** pytest with coverage
- **Test files:** `scripts/tests/test_*.py`
- **Coverage target:** 100% for all modules under `scripts/`
- **Command:** `uv run pytest --cov=scripts --cov-report=term-missing -q scripts/tests`

### Frontend Unit Tests

- **Framework:** Jest + React Testing Library
- **Test files:** `wireframe-ui/__tests__/page.test.tsx`
- **Command:** `npm test` (in `wireframe-ui/`)

### Frontend E2E Tests

- **Framework:** Playwright
- **Trigger:** Hydration-sensitive changes require E2E
- **Command:** `make ui-e2e`

### Quality Gate

`make ui-verify` is the blocking gate for all `wireframe-ui/` changes. It includes:

- Unit tests
- Typecheck
- Clean build (clears `.next`)
- Runtime smoke against the built app (`UI_SMOKE_MODE=start`)
- Playwright E2E

---

## 17. Operational Guide

### CLI Workflow (Backward-Compatible)

```bash
# 1. Fetch tickets
uv run python scripts/get_tickets.py -a \
  --jql-file scripts/jql/hpc_default.jql -y

# 2. Normalize
uv run python scripts/normalize_tickets.py -y

# 3. Categorize
uv run python scripts/rule_engine_categorize.py \
  --tickets-dir scripts/normalized-tickets/<date> \
  --rule-engine scripts/trained-data/golden-rules-engine/rule-engine.csv \
  --output-dir scripts/analysis -y

# 4. Audit
# Review scripts/analysis/tickets-categorized.csv

# 5. Train (LLM rule generation)
uv run python scripts/run_training.py \
  --tickets-categorized scripts/analysis/tickets-categorized.csv \
  --rules-engine-file scripts/trained-data/rule-engine.local.csv \
  --prompt-file prompts/training.md \
  --engine codex -y

# 6. Re-categorize with updated rules

# 7. Promote to golden (manual)
```

### Wireframe UI Workflow

1. Start UI: `cd wireframe-ui && npm ci && PATH="../.venv/bin:$PATH" npm run dev`
2. Open `http://localhost:3000`
3. Choose workflow: Categorize, Train STC, Add Rule, Browse, Promote
4. For Train STC: configure skip-audit checkboxes (default: both skipped), enter JQL, click OK
5. Pipeline runs with real-time logs, pause points (if not skipped), and result display

### One-Command Helper

```bash
scripts/run_training_loop.sh \
  --start-date 2026-02-10 \
  --end-date 2026-02-12 \
  --jql-file scripts/jql/hpc_default.jql \
  --rule-engine scripts/trained-data/rule-engine.local.csv \
  --yes
```

---

## 18. Future Considerations

- **Dashboard UI with charts** — React + Recharts for trend visualization
- **Batch API Integration** — high-volume processing endpoint
- **Database Migration** — SQLite or PostgreSQL for query flexibility
- **Automated Scheduling** — cron-based daily runs
- **Multi-Region Expansion** — beyond AGA to other data center regions
- **Rule Engine Versioning** — changelog and diff history for rule changes
- **CI/CD Pipeline** — automated testing and deployment
- **Active Learning Loop** — ML model retraining from new audit data
