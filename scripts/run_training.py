#!/usr/bin/env python3
# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted
"""Generate local rule-engine proposals from audited ticket feedback.

Supports multiple rule-generation engines via --engine:
  codex    — use Codex AI to propose rules (default, requires --prompt/--prompt-file)
  ml       — use the trained ML classifier to propose rules (fast, no Codex needed)
  codex+ml — run both engines and merge proposals

Usage:
    # Codex only (existing behavior)
    python3 scripts/run_training.py \
        --tickets-categorized scripts/analysis/tickets-categorized.csv \
        --rules-engine-file scripts/trained-data/golden-rules-engine/rule-engine.csv \
        --prompt-file prompts/training.md

    # ML only (fast, no Codex dependency)
    python3 scripts/run_training.py \
        --tickets-categorized scripts/analysis/tickets-categorized.csv \
        --rules-engine-file scripts/trained-data/golden-rules-engine/rule-engine.csv \
        --engine ml \
        --ml-model scripts/trained-data/ml-model/classifier.joblib \
        --ml-category-map scripts/trained-data/ml-model/category_map.json

    # Both engines
    python3 scripts/run_training.py \
        --tickets-categorized scripts/analysis/tickets-categorized.csv \
        --rules-engine-file scripts/trained-data/golden-rules-engine/rule-engine.csv \
        --engine codex+ml \
        --prompt-file prompts/training.md \
        --ml-model scripts/trained-data/ml-model/classifier.joblib \
        --ml-category-map scripts/trained-data/ml-model/category_map.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from io import TextIOBase
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_RULE_ENGINE = (
    REPO_ROOT / "scripts" / "trained-data" / "rule-engine.local.csv"
)

REQUIRED_TICKET_COLUMNS = {
    "Ticket",
    "Project Key",
    "Ticket Description",
    "Category of Issue",
    "Category",
    "Human Audit for Accuracy",
    "Human Comments",
}

RULE_ENGINE_COLUMNS = (
    "Project Key",
    "RuleID",
    "Rule Pattern",
    "Match Field",
    "Failure Category",
    "Category",
    "Priority",
    "Confidence",
    "Created By",
    "Hit Count",
)

RULE_ID_RE = re.compile(r"^R(\d+)$")
CODEX_BIN = "codex"
DEFAULT_CODEX_TIMEOUT_SEC = 120
HEARTBEAT_INTERVAL_SEC = 10
JSON_ERROR_PREVIEW_CHARS = 1000
AUDIT_VERDICTS_TO_REVIEW = {"incorrect", "needs-review"}
ENGINE_CODEX = "codex"
ENGINE_ML = "ml"
ENGINE_CODEX_ML = "codex+ml"
ENGINE_CHOICES = (ENGINE_CODEX, ENGINE_ML, ENGINE_CODEX_ML)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Generate local rule-engine updates from audited tickets. "
            "Rows marked incorrect/needs-review with comments are used."
        )
    )
    parser.add_argument("--tickets-categorized", required=True, type=Path,
                        help="Path to tickets-categorized.csv")
    parser.add_argument("--rules-engine-file", required=True, type=Path,
                        help="Source rule-engine CSV")
    parser.add_argument(
        "--engine",
        choices=ENGINE_CHOICES,
        default=ENGINE_CODEX,
        help=(
            "Rule generation engine: codex (default), ml, or codex+ml. "
            "Use 'ml' for fast ML-only rule generation without Codex. "
            "Use 'codex+ml' to run both engines and merge proposals."
        ),
    )
    parser.add_argument(
        "--prompt",
        help=(
            "Inline prompt text to send to Codex. "
            "If this value is a path to an existing file, it will be read as markdown input. "
            "Only required when --engine includes codex."
        ),
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Path to a prompt markdown file. Only required when --engine includes codex.",
    )
    parser.add_argument(
        "--ml-model", type=Path, default=None,
        help="Path to trained ML classifier (.joblib). Required when --engine includes ml.",
    )
    parser.add_argument(
        "--ml-category-map", type=Path, default=None,
        help="Path to category_map.json for ML classifier. Required when --engine includes ml.",
    )
    parser.add_argument(
        "--tickets-dir", type=Path, default=None,
        help=(
            "Directory with normalized ticket JSONs for ML rule generation. "
            "Auto-detects the most recent date folder if omitted."
        ),
    )
    parser.add_argument(
        "--auto-rules",
        action="store_true",
        help=(
            "Auto-generate rules from all non-rule-matched tickets without "
            "waiting for human audit. When set with --engine ml or codex+ml, "
            "the ML processes all ML-categorized and uncategorized tickets "
            "instead of only human-reviewed rows."
        ),
    )
    parser.add_argument(
        "--output-rule-engine", type=Path,
        default=DEFAULT_OUTPUT_RULE_ENGINE,
        help=(
            "Path for output local rule-engine copy. "
            "Default: scripts/trained-data/rule-engine.local.csv"
        ),
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help=(
            "Path to run log file. If omitted, writes to "
            "scripts/logs/run_training_<UTC timestamp>.log"
        ),
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip estimated-runtime confirmation prompt and run immediately.",
    )
    parser.add_argument(
        "--codex-timeout",
        type=int,
        default=DEFAULT_CODEX_TIMEOUT_SEC,
        help=(
            "Max seconds to wait for Codex. "
            "Default: 120. Use 0 to wait indefinitely."
        ),
    )
    parser.add_argument(
        "--codex-batch-size",
        type=int,
        default=2,
        help="Number of review rows to send per Codex call. Default: 2.",
    )
    parser.add_argument(
        "--max-review-rows",
        "--max-incorrect-rows",
        dest="max_review_rows",
        type=int,
        default=200,
        help=(
            "Maximum number of review rows (incorrect/needs-review) to process per run. "
            "Default: 200."
        ),
    )
    args = parser.parse_args(argv)
    uses_codex = args.engine in (ENGINE_CODEX, ENGINE_CODEX_ML)
    uses_ml = args.engine in (ENGINE_ML, ENGINE_CODEX_ML)
    if uses_codex and not args.prompt and not args.prompt_file:
        parser.error("--prompt or --prompt-file is required when --engine includes codex")
    if uses_ml:
        if not args.ml_model:
            parser.error("--ml-model is required when --engine includes ml")
        if not args.ml_category_map:
            parser.error("--ml-category-map is required when --engine includes ml")
    if args.max_review_rows <= 0:
        parser.error("--max-review-rows must be a positive integer")
    if args.codex_batch_size <= 0:
        parser.error("--codex-batch-size must be a positive integer")
    return args


def validate_file(path: Path, label: str):
    if not path.is_file():
        sys.exit(f"Error: {label} file not found: {path}")


class _TeeStream(TextIOBase):
    def __init__(self, original, log_handle):
        self._original = original
        self._log_handle = log_handle

    def write(self, s):
        self._original.write(s)
        self._log_handle.write(s)
        return len(s)

    def flush(self):
        self._original.flush()
        self._log_handle.flush()


def resolve_log_file_path(log_file: Path | None, started_at: datetime):
    if log_file is not None:
        return log_file
    stamp = started_at.strftime("%Y%m%dT%H%M%SZ")
    return REPO_ROOT / "scripts" / "logs" / f"run_training_{stamp}.log"


def enable_run_logging(log_file: Path | None, started_at: datetime):
    log_path = resolve_log_file_path(log_file, started_at)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = open(log_path, "w", encoding="utf-8")
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = _TeeStream(original_stdout, log_handle)
    sys.stderr = _TeeStream(original_stderr, log_handle)
    return log_path, log_handle, original_stdout, original_stderr


def disable_run_logging(log_handle, original_stdout, original_stderr):
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    log_handle.close()


def _format_duration(seconds: int):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:d}h {minutes:02d}m {secs:02d}s"


def estimate_runtime_seconds(review_count: int, batch_size: int, timeout_sec: int):
    if review_count <= 0:
        return 0, None, 0
    batches = (review_count + batch_size - 1) // batch_size
    worst_case = batches * timeout_sec if timeout_sec > 0 else None
    estimated = batches * min(45, timeout_sec) if timeout_sec > 0 else batches * 45
    return estimated, worst_case, batches


def confirm_ready_to_run(estimated_sec: int, worst_sec: int | None, batches: int):
    worst_case_text = _format_duration(worst_sec) if worst_sec is not None else "unbounded"
    answer = input(
        "Proceed with run? "
        f"estimated={_format_duration(estimated_sec)}, "
        f"worst_case={worst_case_text}, "
        f"batches={batches} [y/N]: "
    ).strip().lower()
    return answer in {"y", "yes"}


def load_prompt_text(prompt: str | None, prompt_file: Path | None):
    if prompt_file is not None:
        validate_file(prompt_file, "Prompt")
        return prompt_file.read_text(encoding="utf-8")

    if not prompt.strip():
        sys.exit("Error: missing required prompt input. Use --prompt or --prompt-file.")

    prompt_path = Path(prompt)
    try:
        if prompt_path.exists() and prompt_path.is_file():
            return prompt_path.read_text(encoding="utf-8")
    except OSError:
        # Treat non-path-safe values (e.g. very long inline text) as prompt text.
        pass

    return prompt


def load_feedback_rows(path: Path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_TICKET_COLUMNS - headers)
        if missing:
            sys.exit(f"Error: missing required columns in tickets file: {', '.join(missing)}")

        rows = list(reader)

    review_rows = []
    missing_comments_total = 0
    for row in rows:
        verdict = (row.get("Human Audit for Accuracy") or "").strip().lower()
        comments = (row.get("Human Comments") or "").strip()
        if verdict not in AUDIT_VERDICTS_TO_REVIEW:
            continue
        if not comments:
            missing_comments_total += 1
        review_rows.append(row)

    return rows, review_rows, missing_comments_total


def copy_rules_engine(source: Path, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)


def next_rule_id(rule_rows):
    max_id = 0
    for row in rule_rows:
        m = RULE_ID_RE.match((row.get("RuleID") or "").strip())
        if m:
            max_id = max(max_id, int(m.group(1)))
    return max_id + 1


def _read_rule_rows(path: Path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_failure_to_category_map(rule_rows):
    mapping = {}
    for row in rule_rows:
        project = (row.get("Project Key") or "").strip()
        failure = (row.get("Failure Category") or "").strip()
        category = (row.get("Category") or "").strip()
        if not failure or not category or category.lower() == "unknown":
            continue
        key = (project.lower(), failure.lower())
        if key not in mapping:
            mapping[key] = category
    return mapping


def infer_category_from_failure(
    project_key: str,
    failure_category: str,
    failure_to_category: Dict[tuple[str, str], str],
):
    project = (project_key or "").strip().lower()
    failure = (failure_category or "").strip().lower()
    if not failure:
        return None

    project_match = failure_to_category.get((project, failure))
    if project_match:
        return project_match
    return failure_to_category.get(("", failure))


def normalize_proposal(
    proposal: Dict[str, Any],
    project_key: str,
    rule_id: str,
    failure_to_category: Dict[tuple[str, str], str] | None = None,
):
    rule_pattern = (
        proposal.get("Rule Pattern")
        or proposal.get("rule_pattern")
        or proposal.get("pattern")
        or ""
    )
    match_field = (
        proposal.get("Match Field")
        or proposal.get("match_field")
        or proposal.get("match field")
        or "summary+description"
    )
    failure_category = (
        proposal.get("Failure Category")
        or proposal.get("failure_category")
        or proposal.get("category_of_issue")
        or "Unknown Failure"
    )
    category = (
        proposal.get("Category")
        or proposal.get("category")
        or "unknown"
    )
    if (
        isinstance(category, str)
        and category.strip().lower() == "unknown"
        and failure_to_category is not None
    ):
        inferred_category = infer_category_from_failure(
            project_key=project_key,
            failure_category=str(failure_category),
            failure_to_category=failure_to_category,
        )
        if inferred_category:
            print(
                "Inferred category from existing rules: "
                f"failure='{failure_category}' -> category='{inferred_category}'"
            )
            category = inferred_category
    priority_raw = (
        proposal.get("Priority")
        or proposal.get("priority")
        or "80"
    )
    confidence_raw = (
        proposal.get("Confidence")
        or proposal.get("confidence")
        or "1"
    )
    created_by = (
        proposal.get("Created By")
        or proposal.get("created_by")
        or "human-feedback"
    )
    hit_count_raw = (
        proposal.get("Hit Count")
        or proposal.get("hit_count")
        or "0"
    )

    if not rule_pattern:
        return None

    try:
        re.compile(rule_pattern)
    except re.error as exc:
        print(f"Skipping proposal due to invalid regex '{rule_pattern}': {exc}", file=sys.stderr)
        return None

    try:
        priority = int(priority_raw)
    except (TypeError, ValueError):
        priority = 80

    try:
        confidence = float(confidence_raw)
    except (TypeError, ValueError):
        confidence = 1

    try:
        hit_count = int(hit_count_raw)
    except (TypeError, ValueError):
        hit_count = 0

    return {
        "Project Key": project_key,
        "RuleID": rule_id,
        "Rule Pattern": rule_pattern,
        "Match Field": match_field,
        "Failure Category": failure_category,
        "Category": category,
        "Priority": priority,
        "Confidence": confidence,
        "Created By": created_by,
        "Hit Count": hit_count,
    }


def determine_project_key(proposal: Dict[str, Any], project_by_ticket: Dict[str, str]):
    explicit = proposal.get("Project Key") or proposal.get("project_key")
    if explicit:
        return str(explicit).strip()

    ticket_key = proposal.get("Ticket") or proposal.get("ticket")
    if ticket_key:
        return project_by_ticket.get(str(ticket_key), "")

    if len(project_by_ticket) == 1:
        return next(iter(project_by_ticket.values()))
    return ""


def build_codex_input(prompt_text: str, rows):
    feedback_rows = []
    for row in rows:
        feedback_rows.append({
            "Ticket": row.get("Ticket", ""),
            "Project Key": row.get("Project Key", ""),
            "Ticket Description": row.get("Ticket Description", ""),
            "Category of Issue": row.get("Category of Issue", ""),
            "Category": row.get("Category", ""),
            "Human Comments": row.get("Human Comments", ""),
        })

    payload = {
        "feedback_rows": feedback_rows,
    }
    response_contract = (
        "RESPONSE FORMAT (STRICT):\n"
        "Return ONLY valid JSON. Do not include markdown, prose, code fences, or explanations.\n"
        'Required top-level shape: {"proposals": [ ... ]}\n'
        "Each proposal should be an object containing rule fields such as "
        '"Rule Pattern", "Match Field", "Failure Category", and "Category".'
    )
    return (
        f"{prompt_text}\n\n"
        f"{response_contract}\n\n"
        f"INPUT JSON:\n{json.dumps(payload, ensure_ascii=False)}\n"
    )


def _parse_codex_json_output(stdout_text: str):
    text = (stdout_text or "").strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try fenced code blocks first (```json ...``` then generic ```...```).
    for pattern in (r"```json\s*(\{.*?\})\s*```", r"```\s*(\{.*?\})\s*```"):
        for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.DOTALL):
            candidate = match.group(1).strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    # Finally, try the widest JSON object slice in mixed prose output.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None

    return None


def _call_codex_with_reason(prompt_text: str, rows, timeout_sec: int):
    if not rows:
        return [], "no_review_rows"
    payload = build_codex_input(prompt_text, rows)
    command = [
        CODEX_BIN,
        "-a",
        "on-failure",
        "exec",
        "-p",
        "plan",
        "--sandbox",
        "workspace-write",
        "-C",
        str(REPO_ROOT),
    ]
    print(f"Codex command: {shlex.join(command)}")
    run_kwargs = {
        "input": payload,
        "text": True,
        "capture_output": True,
    }
    if timeout_sec > 0:
        run_kwargs["timeout"] = timeout_sec

    started_at = datetime.now(timezone.utc)
    print(f"Codex run started at: {started_at.isoformat()}")
    stop_event = threading.Event()
    start_monotonic = time.monotonic()

    def _heartbeat():
        while not stop_event.wait(HEARTBEAT_INTERVAL_SEC):
            elapsed = int(time.monotonic() - start_monotonic)
            print(f"Heartbeat: Codex still running ({elapsed}s elapsed)...")

    heartbeat_thread = threading.Thread(target=_heartbeat, daemon=True)
    heartbeat_thread.start()

    try:
        result = subprocess.run(command, **run_kwargs)
    except subprocess.TimeoutExpired:
        stop_event.set()
        heartbeat_thread.join(timeout=0.2)
        ended_at = datetime.now(timezone.utc)
        print(f"Codex run ended at: {ended_at.isoformat()}")
        print(f"Codex elapsed: {time.monotonic() - start_monotonic:.2f}s")
        print(
            "Codex timed out while generating rule proposals. "
            f"Increase --codex-timeout from {timeout_sec}s.",
            file=sys.stderr,
        )
        return [], "timeout"
    finally:
        stop_event.set()
        heartbeat_thread.join(timeout=0.2)

    ended_at = datetime.now(timezone.utc)
    print(f"Codex run ended at: {ended_at.isoformat()}")
    print(f"Codex elapsed: {time.monotonic() - start_monotonic:.2f}s")

    if result.returncode != 0:
        print("Codex execution failed:")
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return [], "execution_failed"

    parsed = _parse_codex_json_output(result.stdout or "")
    if parsed is None:
        print("Error: Codex did not return valid JSON.", file=sys.stderr)
        stdout_preview = (result.stdout or "")[:JSON_ERROR_PREVIEW_CHARS]
        stderr_preview = (result.stderr or "")[:JSON_ERROR_PREVIEW_CHARS]
        if stdout_preview:
            print(
                f"Codex stdout preview (first {JSON_ERROR_PREVIEW_CHARS} chars):\n"
                f"{stdout_preview}",
                file=sys.stderr,
            )
        if stderr_preview:
            print(
                f"Codex stderr preview (first {JSON_ERROR_PREVIEW_CHARS} chars):\n"
                f"{stderr_preview}",
                file=sys.stderr,
            )
        return [], "invalid_json"

    proposals = parsed.get("proposals") if isinstance(parsed, dict) else None
    if not isinstance(proposals, list):
        print("Error: Codex JSON must contain a proposals list.", file=sys.stderr)
        return [], "invalid_proposals_shape"

    if not proposals:
        return [], "no_proposals"
    return proposals, "ok"


def call_codex(prompt_text: str, rows, timeout_sec: int):
    proposals, _reason = _call_codex_with_reason(prompt_text, rows, timeout_sec)
    return proposals


def find_latest_tickets_dir():
    """Pick the most recent date folder under scripts/normalized-tickets/."""
    base = REPO_ROOT / "scripts" / "normalized-tickets"
    if not base.is_dir():
        return None
    date_dirs = sorted(d for d in base.iterdir() if d.is_dir())
    return date_dirs[-1] if date_dirs else None


def _load_ticket_jsons(tickets_dir, ticket_keys):
    """Load normalized ticket JSONs for the given ticket keys.

    Returns dict mapping ticket key → parsed JSON dict.
    """
    if not tickets_dir or not tickets_dir.is_dir():
        return {}
    result = {}
    for json_file in tickets_dir.glob("*.json"):
        if json_file.stem in ticket_keys:
            with open(json_file, encoding="utf-8") as f:
                result[json_file.stem] = json.load(f)
    return result


def generate_ml_proposals(review_rows, ml_pipeline, ml_category_map, tickets_dir):
    """Generate rule proposals using the ML classifier.

    For each review row:
    1. Load ticket JSON
    2. Predict category with ML
    3. Extract distinctive TF-IDF terms from ticket text
    4. Build regex pattern from those terms
    5. Create a rule proposal

    Returns a list of proposal dicts (same shape as Codex proposals).
    """
    from ml_classifier import (
        build_feature_text,
        extract_top_terms,
        ML_CONFIDENCE_THRESHOLD,
    )

    ticket_keys = {row.get("Ticket", "").strip() for row in review_rows}
    ticket_data_map = _load_ticket_jsons(tickets_dir, ticket_keys)

    if not ticket_data_map:
        print("  ML: no ticket JSONs found — cannot generate proposals")
        return []

    proposals = []
    for row in review_rows:
        ticket_key = row.get("Ticket", "").strip()
        project_key = row.get("Project Key", "").strip()

        ticket_data = ticket_data_map.get(ticket_key)
        if ticket_data is None:
            print(f"  ML: skipping {ticket_key} — no ticket JSON found")
            continue

        text = build_feature_text(ticket_data)
        if not text.strip():
            print(f"  ML: skipping {ticket_key} — empty feature text")
            continue

        # Predict category
        proba = ml_pipeline.predict_proba([text])[0]
        classes = ml_pipeline.classes_
        best_idx = proba.argmax()
        predicted_coi = classes[best_idx]
        confidence = float(proba[best_idx])
        predicted_category = ml_category_map.get(predicted_coi, "unknown")

        if confidence < ML_CONFIDENCE_THRESHOLD:
            print(f"  ML: skipping {ticket_key} — low confidence ({confidence:.2f})")
            continue

        # Extract top TF-IDF terms for pattern building
        top_terms = extract_top_terms(ml_pipeline, text, n=5)
        if not top_terms:
            print(f"  ML: skipping {ticket_key} — no distinctive terms found")
            continue

        # Prefer terms that appear in the summary (more targeted patterns)
        summary = ticket_data.get("ticket", {}).get("summary", "")
        summary_lower = summary.lower()
        summary_terms = [t for t, _s in top_terms if t.lower() in summary_lower]
        pattern_terms = summary_terms[:3] if summary_terms else [t for t, _s in top_terms[:3]]

        if not pattern_terms:
            continue

        # Build regex: escape terms and join for ordered matching
        escaped = [re.escape(term) for term in pattern_terms]
        if len(escaped) >= 2:
            pattern = ".*".join(escaped[:2])
        else:
            pattern = escaped[0]

        proposals.append({
            "Rule Pattern": pattern,
            "Match Field": "summary+description",
            "Failure Category": predicted_coi,
            "Category": predicted_category,
            "Priority": 70,
            "Confidence": round(confidence, 2),
            "Created By": "ml-generated",
            "Project Key": project_key,
            "Ticket": ticket_key,
        })

        print(
            f"  ML: {ticket_key} -> {predicted_coi} ({predicted_category}) "
            f"conf={confidence:.2f} pattern='{pattern}'"
        )

    return proposals


def append_rules(output_rule_engine: Path, new_rules):
    if not new_rules:
        return

    with open(output_rule_engine, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RULE_ENGINE_COLUMNS)
        for rule in new_rules:
            row = {key: "" for key in RULE_ENGINE_COLUMNS}
            row.update(rule)
            writer.writerow(row)


def main(argv=None):
    args = parse_args(argv)
    script_started_at = datetime.now(timezone.utc)
    run_start_monotonic = time.monotonic()
    log_path, log_handle, original_stdout, original_stderr = enable_run_logging(
        args.log_file, script_started_at
    )

    try:
        print(f"Log file: {log_path}")
        print(f"Run started at: {script_started_at.isoformat()}")

        uses_codex = args.engine in (ENGINE_CODEX, ENGINE_CODEX_ML)
        uses_ml = args.engine in (ENGINE_ML, ENGINE_CODEX_ML)
        print(f"Engine: {args.engine}")

        validate_file(args.tickets_categorized, "Tickets CSV")
        validate_file(args.rules_engine_file, "Rules engine")

        prompt_text = None
        if uses_codex:
            prompt_text = load_prompt_text(args.prompt, args.prompt_file)
            prompt_source = str(args.prompt_file) if args.prompt_file else "inline --prompt"
            prompt_preview = prompt_text.replace("\n", "\\n")
            if len(prompt_preview) > 200:
                prompt_preview = prompt_preview[:200] + "..."
            print(f"Prompt source: {prompt_source}")
            print(f"Prompt chars: {len(prompt_text)}")
            print(f"Prompt preview: {prompt_preview}")

        ml_pipeline = None
        ml_category_map = None
        tickets_dir = None
        if uses_ml:
            from ml_classifier import load_model as ml_load_model
            validate_file(args.ml_model, "ML model")
            validate_file(args.ml_category_map, "ML category map")
            ml_pipeline, ml_category_map = ml_load_model(
                args.ml_model, args.ml_category_map
            )
            tickets_dir = args.tickets_dir or find_latest_tickets_dir()
            print(f"ML model: {args.ml_model}")
            print(f"ML category map: {args.ml_category_map}")
            print(f"Tickets dir: {tickets_dir}")
            if not tickets_dir or not tickets_dir.is_dir():
                print(
                    "WARNING: No tickets directory found. "
                    "ML rule generation requires normalized ticket JSONs.",
                    file=sys.stderr,
                )

        print(f"Max review rows per run: {args.max_review_rows}")
        if uses_codex:
            print(f"Codex batch size: {args.codex_batch_size}")

        all_rows, review_rows, missing_comments_total = load_feedback_rows(
            args.tickets_categorized
        )
        rows_scanned = len(all_rows)
        review_rows = review_rows[:args.max_review_rows]
        review_count = len(review_rows)
        missing_comments_considered = sum(
            1 for row in review_rows if not (row.get("Human Comments") or "").strip()
        )

        # Auto-rules: ML processes all non-rule-matched tickets
        # (ML-categorized + uncategorized) without waiting for human audit
        if args.auto_rules and uses_ml:
            ml_input_rows = [
                row for row in all_rows
                if (row.get("Categorization Source") or "").strip() != "rule"
            ][:args.max_review_rows]
            print(
                f"Auto-rules: {len(ml_input_rows)} non-rule-matched tickets "
                f"(skipped {rows_scanned - len(ml_input_rows)} rule-matched)"
            )
        else:
            ml_input_rows = review_rows

        copy_rules_engine(args.rules_engine_file, args.output_rule_engine)
        existing_rules = _read_rule_rows(args.output_rule_engine)
        failure_to_category = build_failure_to_category_map(existing_rules)
        next_id = next_rule_id(existing_rules)

        if uses_codex:
            est_sec, worst_sec, estimated_batches = estimate_runtime_seconds(
                review_count, args.codex_batch_size, args.codex_timeout
            )
            print(
                "Estimated total runtime: {0} (worst-case: {1})".format(
                    _format_duration(est_sec),
                    _format_duration(worst_sec) if worst_sec is not None else "unbounded",
                )
            )
            print(f"Estimated batches: {estimated_batches}")
            if review_count > 0 and not args.yes:
                if not confirm_ready_to_run(est_sec, worst_sec, estimated_batches):
                    print("Run cancelled by user.")
                    script_ended_at = datetime.now(timezone.utc)
                    print(f"Run ended at: {script_ended_at.isoformat()}")
                    print(f"Elapsed: {time.monotonic() - run_start_monotonic:.2f}s")
                    return {
                        "rows_scanned": rows_scanned,
                        "incorrect_rows": review_count,
                        "skipped": missing_comments_total,
                        "rules_added": 0,
                        "output_rule_engine": str(args.output_rule_engine),
                        "log_file": str(log_path),
                    }

        all_proposals = []
        reason_counts: Dict[str, int] = {}

        # --- ML-based rule generation ---
        if uses_ml and ml_input_rows:
            print("\n--- ML Rule Generation ---")
            ml_proposals = generate_ml_proposals(
                ml_input_rows, ml_pipeline, ml_category_map, tickets_dir
            )
            all_proposals.extend(ml_proposals)
            print(f"ML proposals generated: {len(ml_proposals)}")
            if not ml_proposals:
                reason_counts["ml_no_proposals"] = 1

        # --- Codex-based rule generation ---
        if uses_codex and review_rows:
            print("\n--- Codex Rule Generation ---")
            total_batches = (review_count + args.codex_batch_size - 1) // args.codex_batch_size
            for batch_idx, start in enumerate(range(0, review_count, args.codex_batch_size), start=1):
                batch_rows = review_rows[start:start + args.codex_batch_size]
                print(f"Codex batch {batch_idx}/{total_batches}: rows={len(batch_rows)}")
                proposals, codex_reason = _call_codex_with_reason(
                    prompt_text, batch_rows, args.codex_timeout
                )
                if proposals:
                    all_proposals.extend(proposals)
                else:
                    reason_counts[codex_reason] = reason_counts.get(codex_reason, 0) + 1

        if not review_rows:
            reason_counts["no_review_rows"] = 1

        proposals = all_proposals
        if not proposals:
            no_proposals_reason = ", ".join(
                f"{reason}={count}" for reason, count in sorted(reason_counts.items())
            ) or "unknown"
            print("Rows scanned: {0}".format(rows_scanned))
            print("Review rows considered: {0}".format(review_count))
            print(
                "Review rows with missing comments (considered/total): "
                "{0}/{1}".format(missing_comments_considered, missing_comments_total)
            )
            print(f"No proposals reason: {no_proposals_reason}")
            print("Rules added: 0")
            print(f"Output rule-engine file: {args.output_rule_engine}")
            script_ended_at = datetime.now(timezone.utc)
            print(f"Run ended at: {script_ended_at.isoformat()}")
            print(f"Elapsed: {time.monotonic() - run_start_monotonic:.2f}s")
            return {
                "rows_scanned": rows_scanned,
                "incorrect_rows": review_count,
                "skipped": missing_comments_total,
                "rules_added": 0,
                "output_rule_engine": str(args.output_rule_engine),
                "log_file": str(log_path),
            }

        project_by_ticket = {
            row.get("Ticket", ""): row.get("Project Key", "")
            for row in all_rows
        }

        normalized = []
        current_id = next_id
        for proposal in proposals:
            if not isinstance(proposal, dict):
                continue
            project_key = determine_project_key(proposal, project_by_ticket)
            normalized_rule = normalize_proposal(
                proposal=proposal,
                project_key=project_key,
                rule_id=f"R{current_id:03d}",
                failure_to_category=failure_to_category,
            )
            if normalized_rule is not None:
                normalized.append(normalized_rule)
                current_id += 1

        append_rules(args.output_rule_engine, normalized)

        if normalized:
            print("Rules appended:")
            for rule in normalized:
                print(
                    "  - {rule_id} | project={project} | field={field} | "
                    "failure='{failure}' | category='{category}' | pattern='{pattern}'".format(
                        rule_id=rule.get("RuleID", ""),
                        project=rule.get("Project Key", ""),
                        field=rule.get("Match Field", ""),
                        failure=rule.get("Failure Category", ""),
                        category=rule.get("Category", ""),
                        pattern=rule.get("Rule Pattern", ""),
                    )
                )

        no_proposals_reason = ""
        if proposals and not normalized:
            no_proposals_reason = "all_proposals_rejected"

        print("Rows scanned: {0}".format(rows_scanned))
        print("Review rows considered: {0}".format(review_count))
        print(
            "Review rows with missing comments (considered/total): "
            "{0}/{1}".format(missing_comments_considered, missing_comments_total)
        )
        if no_proposals_reason:
            print(f"No proposals reason: {no_proposals_reason}")
        print("Rules added: {0}".format(len(normalized)))
        print(f"Output rule-engine file: {args.output_rule_engine}")
        script_ended_at = datetime.now(timezone.utc)
        print(f"Run ended at: {script_ended_at.isoformat()}")
        print(f"Elapsed: {time.monotonic() - run_start_monotonic:.2f}s")

        return {
            "rows_scanned": rows_scanned,
            "incorrect_rows": review_count,
            "skipped": missing_comments_total,
            "rules_added": len(normalized),
            "output_rule_engine": str(args.output_rule_engine),
            "log_file": str(log_path),
        }
    finally:
        disable_run_logging(log_handle, original_stdout, original_stderr)


if __name__ == "__main__":
    main()
