# MEMORY.md

## Project Context
- **Purpose:** DC Ops Ticket Categorization (STC) — predict `Category of Issue` and `Category` for HPC/DO tickets, then improve prediction quality via rules, LLM assistance, and human-audit feedback.
- **Stack:** Python scripts (`scripts/`), CSV artifacts, prompt-driven LLM workflows, conventional commits.
- **Test runner:** pytest for scripts, csv-diff tooling for regression comparisons.

## Architectural Decisions
- All ticket ingestion+normalization scripts emit to directories under `scripts/` to avoid polluting repo root.
- Training outputs (`rule-engine.csv`, `tickets-categorized.csv`) live in `scripts/trained-data/`; golden artifacts in `scripts/trained-data/golden-rules-engine/` are read-only until human promotion.
- Prompt (`prompts/training.md`) is the single source of truth for LLM-run instructions; archives retained for context only.
- Generated code or scripts include the `#ai-assisted` disclaimer block to preserve auditability.
- Rule engine rows carry a `Project Key` column so project-specific classifiers can filter applicable rules without duplicating files.
- The golden directory (`scripts/trained-data/golden-rules-engine/`) is immutable for automated workflows; updates happen only via audited, manual promotion.

- Wireframe UI (Next.js 15, React 19) provides a local web interface for all pipeline workflows with real-time log streaming via NDJSON.
- ML classifier (TF-IDF + SGDClassifier, scikit-learn) serves as fallback when no rule matches; confidence threshold 0.4, min samples 20.
- Training pipeline runs in 3 phases with 2 configurable audit pause points (Human Audit #1 after initial categorize, Human Audit #2 after ML categorize); both default to skipped in the UI.
- Outdated docs archived to `docs/archives/`; active reference docs (fault dictionary, MI355X context) remain in `docs/`.

## Assumptions
- Jira export cadence supplies at least 5 fresh tickets per training batch.
- Human auditors are available to review each pass before promoting rules to the golden directory.
- CSV schema definitions in `templates/data-schemes.md` remain authoritative for column ordering and naming.

## Constraints
- Do not write session data into `templates/` or `scripts/trained-data/golden-rules-engine/`.
- Confidence < 0.5 automatically sets `Human Audit for Accuracy = needs-review`; otherwise default to `pending-review`.
- Rule executions must log every firing `RuleID` and propagate the maximum rule confidence to the ticket row.

## Rejected Approaches
- Storing per-session outputs under dated directories was dropped to simplify operator context; live files stay inside `scripts/trained-data/` with numbered snapshots.
- Direct LLM writes to golden rule-engine were rejected because they bypass human audit.

---

## Proposals

<!-- Other roles append here. Architect reviews, merges, and clears. -->
<!-- Format: [role] YYYY-MM-DD — proposal text -->
