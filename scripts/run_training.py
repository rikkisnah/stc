#!/usr/bin/env python3
# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted
"""Generate local rule-engine proposals from audited ticket feedback.

Usage:
    python3 scripts/run_training.py \
        --tickets-categorized scripts/trained-data/tickets-categorized.csv \
        --rules-engine-file scripts/trained-data/golden-rules-engine/rule-engine.csv \
        --prompt-file prompts/update-rule-engine-prompt.md
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
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
DEFAULT_CODEX_TIMEOUT_SEC = 180


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Generate local rule-engine updates from audited tickets. "
            "Only rows marked incorrect with comments are used."
        )
    )
    parser.add_argument("--tickets-categorized", required=True, type=Path,
                        help="Path to tickets-categorized.csv")
    parser.add_argument("--rules-engine-file", required=True, type=Path,
                        help="Source rule-engine CSV")
    parser.add_argument(
        "--prompt",
        help=(
            "Inline prompt text to send to Codex. "
            "If this value is a path to an existing file, it will be read as markdown input."
        ),
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Path to a prompt markdown file.",
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
        "--codex-timeout",
        type=int,
        default=DEFAULT_CODEX_TIMEOUT_SEC,
        help=(
            "Max seconds to wait for Codex. "
            "Default: 180. Use 0 to wait indefinitely."
        ),
    )
    args = parser.parse_args(argv)
    if not args.prompt and not args.prompt_file:
        parser.error("one of the arguments --prompt --prompt-file is required")
    return args


def validate_file(path: Path, label: str):
    if not path.is_file():
        sys.exit(f"Error: {label} file not found: {path}")


def load_prompt_text(prompt: str | None, prompt_file: Path | None):
    if prompt_file is not None:
        validate_file(prompt_file, "Prompt")
        return prompt_file.read_text(encoding="utf-8")

    if not prompt.strip():
        sys.exit("Error: missing required prompt input. Use --prompt or --prompt-file.")

    prompt_path = Path(prompt)
    if prompt_path.exists() and prompt_path.is_file():
        return prompt_path.read_text(encoding="utf-8")

    return prompt


def load_feedback_rows(path: Path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_TICKET_COLUMNS - headers)
        if missing:
            sys.exit(f"Error: missing required columns in tickets file: {', '.join(missing)}")

        rows = list(reader)

    incorrect = []
    skipped_missing_comment = 0
    for row in rows:
        verdict = (row.get("Human Audit for Accuracy") or "").strip().lower()
        comments = (row.get("Human Comments") or "").strip()
        if verdict != "incorrect":
            continue
        if comments:
            incorrect.append(row)
        else:
            skipped_missing_comment += 1

    return rows, incorrect, skipped_missing_comment


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


def normalize_proposal(proposal: Dict[str, Any], project_key: str, rule_id: str):
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
    return f"{prompt_text}\n\nINPUT JSON:\n{json.dumps(payload, ensure_ascii=False)}\n"


def call_codex(prompt_text: str, rows, timeout_sec: int):
    if not rows:
        return []
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
    run_kwargs = {
        "input": payload,
        "text": True,
        "capture_output": True,
    }
    if timeout_sec > 0:
        run_kwargs["timeout"] = timeout_sec

    try:
        result = subprocess.run(command, **run_kwargs)
    except subprocess.TimeoutExpired:
        print(
            "Codex timed out while generating rule proposals. "
            f"Increase --codex-timeout from {timeout_sec}s.",
            file=sys.stderr,
        )
        return []

    if result.returncode != 0:
        print("Codex execution failed:")
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return []

    try:
        parsed = json.loads((result.stdout or "").strip())
    except json.JSONDecodeError:
        print("Error: Codex did not return valid JSON.", file=sys.stderr)
        return []

    proposals = parsed.get("proposals") if isinstance(parsed, dict) else None
    if not isinstance(proposals, list):
        print("Error: Codex JSON must contain a proposals list.", file=sys.stderr)
        return []

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

    validate_file(args.tickets_categorized, "Tickets CSV")
    validate_file(args.rules_engine_file, "Rules engine")

    prompt_text = load_prompt_text(args.prompt, args.prompt_file)

    all_rows, incorrect_rows, skipped_missing_comments = load_feedback_rows(
        args.tickets_categorized
    )
    rows_scanned = len(all_rows)
    incorrect_count = len(incorrect_rows)

    copy_rules_engine(args.rules_engine_file, args.output_rule_engine)
    existing_rules = _read_rule_rows(args.output_rule_engine)
    next_id = next_rule_id(existing_rules)

    proposals = call_codex(prompt_text, incorrect_rows, args.codex_timeout)
    if not proposals:
        print("Rows scanned: {0}".format(rows_scanned))
        print("Incorrect rows considered: {0}".format(incorrect_count))
        print("Rows skipped (missing comments): {0}".format(skipped_missing_comments))
        print("Rules added: 0")
        print(f"Output rule-engine file: {args.output_rule_engine}")
        return {
            "rows_scanned": rows_scanned,
            "incorrect_rows": incorrect_count,
            "skipped": skipped_missing_comments,
            "rules_added": 0,
            "output_rule_engine": str(args.output_rule_engine),
        }

    project_by_ticket = {
        row.get("Ticket", ""): row.get("Project Key", "")
        for row in incorrect_rows
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
        )
        if normalized_rule is not None:
            normalized.append(normalized_rule)
            current_id += 1

    append_rules(args.output_rule_engine, normalized)

    print("Rows scanned: {0}".format(rows_scanned))
    print("Incorrect rows considered: {0}".format(incorrect_count))
    print("Rows skipped (missing comments): {0}".format(skipped_missing_comments))
    print("Rules added: {0}".format(len(normalized)))
    print(f"Output rule-engine file: {args.output_rule_engine}")

    return {
        "rows_scanned": rows_scanned,
        "incorrect_rows": incorrect_count,
        "skipped": skipped_missing_comments,
        "rules_added": len(normalized),
        "output_rule_engine": str(args.output_rule_engine),
    }


if __name__ == "__main__":
    main()
