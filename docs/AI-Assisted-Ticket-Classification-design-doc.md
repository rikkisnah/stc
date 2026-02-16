<!-- Code was generated via OCI AI and was reviewed by a human SDE -->
<!-- Tag: #ai-assisted -->

# AI-Assisted Ticket Classification (STC)
## Detailed Design Document (Architectural + Operational View)

**Document intent:** Provide a production-oriented technical design for architects and senior developers describing the STC codebase, system behavior, design patterns, and training pipeline.

---

# Document Control

| Field | Value |
|---|---|
| **Title** | AI-Assisted Ticket Classification (STC) Detailed Design |
| **Version** | 1.1 |
| **Author** | Rik Kisnah |
| **Date** | February 16, 2026 |
| **System** | Smart Triager Classifier (STC) |
| **Classification** | Internal |
| **References** | `docs/pdfs_docs/AI-Assisted-Ticket-Classification-HLD.docx`, `docs/training-runbook.md`, `docs/human-audit-playbook.md` |

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem, Domain, and Goals](#2-problem-domain-and-goals)
3. [Architecture Principles and Design Pattern](#3-architecture-principles-and-design-pattern)
4. [System Architecture](#4-system-architecture)
5. [Repository Layout (Operational Boundaries)](#5-repository-layout-operational-boundaries)
6. [Data Model and Schema Contracts](#6-data-model-and-schema-contracts)
7. [Training and Inference Pipeline](#7-training-and-inference-pipeline)
8. [Core Component Behavior](#8-core-component-behavior)
9. [Confidence and Triage Rules](#9-confidence-and-triage-rules)
10. [Runbook Detection Pattern](#10-runbook-detection-pattern)
11. [API and UI Integration](#11-api-and-ui-integration)
12. [Failure Modes and Resilience](#12-failure-modes-and-resilience)
13. [Security, Governance, and Compliance](#13-security-governance-and-compliance-considerations)
14. [Testing and Quality Gates](#14-testing-and-quality-gates)
15. [Non-Functional Characteristics](#15-non-functional-characteristics)
16. [Training Quick Reference (CLI)](#16-training-quick-reference-cli)
17. [Future Architecture Evolution](#17-future-architecture-evolution)
18. [RACI for Domain Ownership](#17-raci-for-domain-ownership)
19. [Architectural Decision Record](#18-architectural-decision-record-adr)
20. [Risks and Mitigations](#20-risks-and-mitigations)
21. [Current Pipeline Health Targets](#21-appendix-current-pipeline-health-targets)

---

# 1. Executive Summary

STC is a file-driven ticket triage platform that classifies Jira incidents into standard `Category of Issue` and `Category` values with human-reviewed accuracy. The architecture combines:

- **Deterministic rule engine** as primary path
- **Statistical ML fallback** for previously unseen patterns
- **LLM-assisted rule generation** to improve recall over time
- **Human-in-the-loop audit gates** for governance and safe learning
- **UI-driven orchestration** for execution and observability

### Why this pattern

The design avoids monolithic AI dependency by delegating final categorization to deterministic artifacts (rules + structured CSV outputs), with ML and LLM used as augmentation layers. This yields predictable output, auditable decisions, and controlled rollout.

---

# 2. Problem, Domain, and Goals

## 2.1 Problem Statement

- Manual ticket triage is slow and inconsistent across engineers.
- Current classification quality depends on individual judgment and can drift.
- Historical runbook-related signals are under-utilized during triage.
- Reproducibility and auditability are required for leadership reporting and process reviews.

## 2.2 Business Goals

1. Reduce human effort for 100-ticket runs to under ~10 minutes on a typical batch.
2. Produce explainable results (`Rules Used`, `Categorization Source`, confidence fields).
3. Ensure reviewable and reversible learning through snapshot-driven regression.
4. Keep operations lightweight (no DB dependency) while enabling future scale.

## 2.3 Functional Goals

- Fetch tickets from Jira by configurable JQL.
- Normalize raw tickets into stable schema for deterministic processing.
- Classify tickets using rules first, then ML fallback.
- Generate and apply new rules through LLM training loops.
- Support audit workflows and controlled promotion to golden rules.
- Provide local UI controls and logs for every stage.

---

# 3. Architecture Principles and Design Pattern

STC applies a **Hexagonal/Layered hybrid** around a plugin-like script backend:

- **Domain layer (business intent):** triage categories, audit states, runbook detection, confidence policy.
- **Application layer (workflows):** scripts for ingestion, normalization, categorize, train, promote.
- **Infrastructure layer (adapters):** Jira API calls, filesystem persistence, CLI execution, LLM CLI wrappers, web UI adapters.
- **Ports/Adapters boundaries:** script inputs/outputs are normalized artifacts (JSON/CSV), enabling independent testing and local replay.

### Core design patterns in codebase

- **Pipeline orchestration pattern:** ordered phase progression with checkpoints/pause points.
- **Rule engine strategy:** ordered pattern-match list with priority and source-of-truth propagation.
- **Fail-safe fallback:** deterministic rule path fails to ML path when no match.
- **Human-in-the-loop governance:** no rule promotion without structured manual review intent.
- **Snapshot/Regression pattern:** suffix-versioned CSVs preserve each pass for reproducibility.

---

# 4. System Architecture

## 4.1 High-level Data & Control Flow

```text
Jira/JQL Input
   |
   v
[1] Ticket Ingestion
   -> scripts/tickets-json/
   |
   v
[2] Normalization
   -> scripts/normalized-tickets/<date>/
   |
   v
[3] Categorization (Rule + ML)
   -> scripts/analysis/
   |
   v
[4] Human Audit (optional / configurable)
   |
   v
[5] ML Train + Rule Engine Train (LLM)
   -> scripts/trained-data/
   |
   v
[6] Re-categorization, Validation, Promotion
   -> scripts/trained-data/rule-engine.csv
   |
   v
[7] Reporting / Export / Review
```

## 4.2 Subsystem View

```text
+-----------------------------------------------------------+
|                    Wireframe UI (Next.js)                  |
| - Trigger pipelines                                      |
| - Stream logs (NDJSON)                                   |
| - Render progress and pauses                               |
| - Persist outputs to analysis/golden directories            |
+-------------------------+-----------------------+-------------+
                          | API routes
                          |
+-------------------------v-----------------------+-------------+
| Python Script Runtime (scripts/ domain)          |             |
| - get_tickets.py                               |             |
| - normalize_tickets.py                          |             |
| - rule_engine_categorize.py                     |             |
| - ml_train.py / ml_classifier.py                |             |
| - run_training.py                                
+-------------------------+-----------------------+-------------+
                          |
                          | Reads/writes
+-------------------------v-------------------------------------+
|             Filesystem Artifacts (No DB)                  |
| scripts/tickets-json, normalized-tickets, trained-data,    |
| analysis/ui-runs, templates, snapshots                    |
+-----------------------------------------------------------+
```

---

# 5. Repository Layout (Operational Boundaries)

```text
stc/
  README.md / AGENTS.md / CLAUDE.md / MEMORY.md / TASKS.md
  scripts/
  wireframe-ui/
  templates/
  prompts/
  docs/
  SKILLS/
```

### Script surface under `scripts/`

- `get_tickets.py` — Jira fetch and raw JSON materialization.
- `normalize_tickets.py` — stable transformation to normalized ticket JSON.
- `rule_engine_categorize.py` — rule + ML classification, output generation.
- `ml_train.py`, `ml_classifier.py` — TF-IDF + SGD training/predict path.
- `run_training.py` — LLM-assisted rule update loop.
- `run_training_loop.sh` — orchestration convenience wrapper.
- `create_summary.py` and `create_rule_from_ticket.py` — support workflows.
- `scripts/tests/` — pytest coverage suite.

### UI surface under `wireframe-ui/`

- `app/page.tsx` and UI workflows for categorize/train/add-rule and artifact browsing.
- API routes for script orchestration and file operations.
- Runtime artifacts under `scripts/analysis/ui-runs/`.

---

# 6. Data Model and Schema Contracts

## 6.1 Rule artifact: `rule-engine*.csv`

Columns (current production model):

- `Project Key`
- `RuleID`
- `Rule Pattern`
- `Match Field`
- `Failure Category`
- `Category`
- `Priority`
- `Confidence`
- `Created By`
- `Hit Count`

### Semantics

- **Priority**: lower value = higher precedence.
- **Confidence**: numeric quality score of match/pattern and provenance.
- **Match Field**: one or more ticket fields, combined as needed.
- **Created By**: provenance for governance (e.g., `human-confirmed`, `llm-suggested`).

## 6.2 Classified output: `tickets-categorized.csv`

- `Project Key`, `Ticket`, `Ticket URL`, `Ticket Description`
- `Status`, `Created`, `Age`, `Runbook Present`
- `Category of Issue`, `Category`
- `Rules Used`, `Categorization Source`
- `LLM Confidence`
- `Human Audit for Accuracy`, `Human Audit Guidance`, `Human Comments`

### Audit governance columns

- `needs-review`: auto-assigned when confidence is weak.
- `pending-review`: acceptable for review but not corrected automatically.
- `correct / incorrect`: final human verdict in audit workflow.

## 6.3 Training source: `ml-training-data.csv`

- `Ticket`, `Category of Issue`, `Category`, `Label Source`, `Label Date`, `Notes`
- Derived from rule-confirmed and audited outcomes for supervised training.

---

# 7. Training and Inference Pipeline

## 7.1 End-to-end training lifecycle

### Phase 1 — Baseline categorization

1. Pull tickets (`get_tickets.py`).
2. Normalize (`normalize_tickets.py`).
3. Categorize against local/golden rules.
4. Optional human audit #1.

### Phase 2 — ML enrichment

5. Train ML model from labeled rows (`ml_train.py`).
6. Re-run categorization with ML fallback (`rule_engine_categorize.py --ml-model`).
7. Optional human audit #2.

### Phase 3 — Rule induction

8. Run LLM-assisted training (`run_training.py`) over incorrect/low-trust rows.
9. Apply newly generated rule set to local rules.
10. Final recategorization and regression checks.

### Promotion path

11. Promote approved local rule set into golden rules (read-only boundary before manual audit approval).
12. Validate by re-run; compare with archived pass CSVs.

## 7.2 How to train (operational detail)

- Inputs: categorized CSV + training metadata.
- Model: TF-IDF text features over `summary`, `description`, `labels`, `comments`.
- Classifier: `SGDClassifier` with probability-style confidence mapping.
- Minimum sample threshold: gate training if class support is insufficient.
- ML output only used when rule match fails.
- Audit-driven loops determine whether generated rules are accepted.

## 7.3 Training quality controls

- Every generated rule is traceable via provenance and review columns.
- Rule updates should be compared against pass-snapshot for regression stability.
- Confidence propagation and thresholds drive audit pressure and workload distribution.

---

# 8. Core Component Behavior

## 8.1 Rule Engine

- Iterate rules in ascending priority.
- Build candidate text from configured ticket fields.
- Case-insensitive regex match with explicit pattern ownership (`Match Field`).
- Compute applied-rule set and select category from matched highest-priority/ highest-confidence policy.
- Set `Rules Used`, `Categorization Source`, confidence fields.
- Optionally apply runbook flags independently (`Runbook Present`) from meta-rules.

## 8.2 ML Classifier

- Uses supervised model artifacts (`classifier.joblib`, `category_map.json`).
- Returns top class and confidence score.
- If score below threshold, classification remains `uncategorized` and is eligible for manual correction.

## 8.3 LLM Training Loop

- Reads audit-labeled rows and identifies weak/incorrect records.
- Produces candidate rule updates via prompt-driven generation (`prompts/training.md`).
- Writes updates into local rule file and supports batch execution for controlled throughput.
- Human audit remains the release gate before promotion.

---

# 9. Confidence and Triage Rules

| Source | Confidence Mechanism |
|---|---|
| Rule match | Maximum confidence among matched rules. |
| ML fallback | Class probability score (top predicted class). |
| LLM suggestion | Inferred confidence of generated output. |

### Default policy

- `LLM Confidence < 0.5` → mark `needs-review`.
- `LLM Confidence >= 0.5` → `pending-review`.

This policy ensures low-confidence rows are surfaced quickly without blocking throughput.

---

# 10. Runbook Detection Pattern

Runbook-related signals are handled as metadata extraction rules that may set `Runbook Present` without forcing category outcome unless explicit policy requires. Typical signals include TRS labels, prescription phrases, and known remediation actions.

---

# 11. API and UI Integration

## 11.1 UI workflow endpoints

- `POST /api/run-jql` — ingestion + normalize + categorize + summary.
- `POST /api/train-stc` — multi-phase training with pause points.
- `POST /api/add-rule-from-ticket` — interactive rule authoring.
- `GET /api/list-files`, `/api/open-file`, `/api/save-file`, `/api/tickets-json` — sandboxed artifact access.

All endpoints return NDJSON event streams for real-time UX (`pipeline-start`, `command-start`, `stdout`, `stderr`, `command-end`, `done`, `error`, `paused`, `canceled`).

## 11.2 Run semantics

- Human-audit pauses are configurable in UI, defaulting to skip for rapid iteration.
- Commands executed from UI inherit cancellation semantics (SIGTERM to child process).
- All run outputs are persisted under `scripts/analysis/ui-runs/<run-id>/`.

---

# 12. Failure Modes and Resilience

- **No rule match:** ML fallback path executes (if model available). If absent or low confidence, remains unresolved for audit.
- **Sparse training data:** ML training is gated and model confidence remains conservative.
- **LLM generation failures:** Existing rule set remains unchanged; pipeline can proceed or fail fast depending on phase.
- **Human-audit skip mode:** Fast execution, but lower assurance; suited for dev/testing cycles only.
- **Schema drift:** Templates and normalized fields are expected to be source-of-truth for compatibility.

---

# 13. Security, Governance, and Compliance Considerations

- Jira credentials and environment values are externalized (`env.json`) and should not be committed.
- Golden rules are treated as production governed artifacts and not modified automatically.
- Outputs are file-based and audit-retained for traceability.
- LLM/ML recommendations are advisory until reviewed and promoted.

---

# 14. Testing and Quality Gates

## 14.1 Backend Python

- pytest suite in `scripts/tests/`.
- Coverage expectation: changed modules should target full line coverage under enforced workflow.
- Command example: `uv run pytest --cov=scripts --cov-report=term-missing -q scripts/tests`

## 14.2 Frontend

- Unit: `wireframe-ui/__tests__/`.
- Smoke + E2E gate: `make ui-verify` (required for frontend changes).
- Runtime + Playwright validation: `make ui-e2e` where hydration-sensitive changes occur.

## 14.3 Regression discipline

- For each promotion cycle: rerun categorization and compare against archived pass CSV to confirm deterministic stability.

---

# 15. Non-Functional Characteristics

- **Determinism:** same normalized inputs + same rules yield stable outputs.
- **Observability:** NDJSON logs, run timestamps, run-id artifact folders.
- **Extensibility:** pattern-based rule engine and prompt-based LLM training decouple model evolution from ticket ingestion.
- **Maintainability:** scripts + templates isolate evolving domain rules from application control flow.

---

# 16. Training Quick Reference (CLI)

```bash
# fetch
uv run python scripts/get_tickets.py -a --jql-file scripts/jql/hpc_default.jql -y

# normalize
uv run python scripts/normalize_tickets.py -y

# categorize
uv run python scripts/rule_engine_categorize.py \
  --tickets-dir scripts/normalized-tickets/<date> \
  --rule-engine scripts/trained-data/golden-rules-engine/rule-engine.csv \
  --output-dir scripts/analysis -y

# train rules from audit output
uv run python scripts/run_training.py \
  --tickets-categorized scripts/analysis/tickets-categorized.csv \
  --rules-engine-file scripts/trained-data/rule-engine.local.csv \
  --prompt-file prompts/training.md \
  --engine <provider> -y
```

One-command helper:

```bash
scripts/run_training_loop.sh \
  --start-date 2026-02-10 \
  --end-date 2026-02-12 \
  --jql-file scripts/jql/hpc_default.jql \
  --rule-engine scripts/trained-data/rule-engine.local.csv \
  --yes
```

---

# 17. Future Architecture Evolution

- Introduce richer workflow state store (SQLite/PostgreSQL) while preserving CSV-compatible import/export.
- Add active-learning scheduler for periodic model retrains.
- Add explicit rule-version metadata and diff UI.
- Add structured metrics instrumentation and drift dashboards.
- Add API-level authentication and stronger run sandboxing for multi-user environments.

---

# 18. RACI for Domain Ownership

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Ticket ingestion and normalization | SRE / Platform Engineer | Technical Lead | UI Owner, Data Owner | Product Owner |
| Rule design and updates | Data / AI Engineer | Data Lead | Domain SMEs, TPM | Operations |
| ML training and model tuning | ML Engineer | Technical Lead | Data/AI Engineer, AI Lead | Product Owner |
| Human audit process execution | TPM / QA | Product Owner | SRE, Data Lead | All engineering stakeholders |
| UI command orchestration and run telemetry | Frontend Owner | Product Owner | SRE / Security | TPM |
| Promotion to golden rules | Data Lead | Architecture Lead | TPM, QA Lead | Platform Governance |
| Regression and release validation | QA Lead | Product Owner | Frontend Owner, Platform Ops | Management |

Role intent:

- **Responsible**: executes the activity.
- **Accountable**: final decision-maker for correctness and timing.
- **Consulted**: two-way input required before completion.
- **Informed**: receives outcome updates for coordination.

---

# 19. Architectural Decision Record (ADR)

## ADR-001: File-system artifacts as the core persistence mechanism

- **Context:** The system needed quick iteration, reproducibility, and transparent audit trails without external DB operations overhead.
- **Decision:** Use canonical CSV/JSON under `scripts/` as the operational state and run output store.
- **Alternatives considered:** PostgreSQL/MySQL (centralized queryability), object storage-backed metadata service (better scale, higher ops overhead).
- **Consequence:** Faster onboarding and simpler local reproduction at the cost of query ergonomics and concurrent-write complexity.
- **Acceptance:** Must enforce deterministic naming, snapshots, and run isolation via `scripts/analysis/ui-runs/<run-id>/`.

## ADR-002: Rule-first deterministic classification before probabilistic ML fallback

- **Context:** Tickets require explainable outcomes and governance assurance.
- **Decision:** Apply the rule engine first and use ML only when no rule matches.
- **Alternatives considered:** ML-first with rule override, or ensemble weighting between rule and ML.
- **Consequence:** Higher explainability and easier audit; slower adaptation to entirely new wording until rule induction catches up.
- **Acceptance:** Rule coverage and confidence KPIs must remain visible in every run report.

## ADR-003: Human-in-the-loop promotion gate for LLM-generated rules

- **Context:** LLM suggestions improve coverage but carry quality risk.
- **Decision:** Keep LLM as rule generator only; require human audit before promotion.
- **Alternatives considered:** Automatic LLM auto-publish, or confidence-only gating without manual approval.
- **Consequence:** Safer rollout with lower operational risk and slower throughput of low-confidence proposals.
- **Acceptance:** No rule reaches golden set without explicit audit workflow completion and regression validation.

## ADR-004: Skip-audit default in UI for fast local iteration

- **Context:** Engineering teams need quick experimentation cycles.
- **Decision:** Keep both audit checkpoints skippable by default in local training UI.
- **Alternatives considered:** Always-on mandatory audits, or always-skipped mode with no pause telemetry.
- **Consequence:** Faster experimentation while preserving optional governance for production-like runs.
- **Acceptance:** Team policy requires explicit mode labeling and justification for non-review skips.

---

# 20. Risks and Mitigations

- **Rule overfitting:** rotate and audit high-confidence/lossless rules; prioritize specificity and sample size.
- **LLM hallucinated patterns:** strict review gate and regression checks before golden promotion.
- **ML degradation:** monitor class distribution and recalibrate threshold by batch cohort.
- **UI-script drift:** enforce runtime smoke + end-to-end gates and clear artifact isolation.

---

# 21. Appendix: Current Pipeline Health Targets

- Categorization time < 10 minutes for 100 tickets.
- Rule coverage > 80% of tickets where possible.
- Human-audited accuracy target > 90%.
- Runbook detection false negative minimized.
- Regression pass required for each promoted rule set.
