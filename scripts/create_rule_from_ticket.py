#!/usr/bin/env python3
# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted
"""Interactively create a rule from a single ticket and optionally append it.

Usage:
    python3 scripts/create_rule_from_ticket.py
    python3 scripts/create_rule_from_ticket.py \
        --rules-engine scripts/trained-data/rule-engine.local.csv
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TICKETS_JSON_DIR = REPO_ROOT / "scripts" / "tickets-json"
DEFAULT_NORMALIZED_ROOT = REPO_ROOT / "scripts" / "normalized-tickets"
DEFAULT_RULES_ENGINE = REPO_ROOT / "scripts" / "trained-data" / "rule-engine.local.csv"
RULE_ID_RE = re.compile(r"^R(\d+)$")
TICKET_KEY_RE = re.compile(r"^[A-Z]+-\d+$")

REQUIRED_RULE_COLUMNS = {
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
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "we",
    "with",
}


def parse_args(argv=None):
    """Parse CLI args."""
    parser = argparse.ArgumentParser(
        description="Create a local rule-engine entry from one ticket interactively."
    )
    parser.add_argument(
        "--ticket-json-dir",
        type=Path,
        default=DEFAULT_TICKETS_JSON_DIR,
        help=f"Directory containing raw ticket JSON files (default: {DEFAULT_TICKETS_JSON_DIR})",
    )
    parser.add_argument(
        "--normalized-root",
        type=Path,
        default=DEFAULT_NORMALIZED_ROOT,
        help=f"Root directory containing dated normalized folders (default: {DEFAULT_NORMALIZED_ROOT})",
    )
    parser.add_argument(
        "--rules-engine",
        type=Path,
        default=DEFAULT_RULES_ENGINE,
        help=f"Local rules CSV to append (default: {DEFAULT_RULES_ENGINE})",
    )
    parser.add_argument(
        "--match-field-default",
        default="summary+description",
        help="Default Match Field value when prompt is left blank.",
    )
    parser.add_argument(
        "--priority",
        type=int,
        default=85,
        help="Priority for the new rule (default: 85).",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=1.0,
        help="Confidence for the new rule (default: 1.0).",
    )
    parser.add_argument(
        "--created-by",
        default="human-feedback",
        help="Created By value for the new rule (default: human-feedback).",
    )
    parser.add_argument(
        "--hit-count",
        type=int,
        default=0,
        help="Initial Hit Count value (default: 0).",
    )
    return parser.parse_args(argv)


def prompt_required(
    prompt_text: str,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[..., None] = print,
):
    """Prompt until a non-empty value is provided."""
    while True:
        value = input_fn(prompt_text).strip()
        if value:
            return value
        print_fn("Value is required.")


def validate_ticket_key(ticket_key: str):
    """Validate ticket key format."""
    if not TICKET_KEY_RE.match(ticket_key):
        raise SystemExit(f"Invalid ticket key: {ticket_key}")


def load_ticket_json(path: Path, label: str):
    """Load JSON payload from path with friendly errors."""
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(f"{label} JSON not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse {label} JSON: {path}") from exc


def find_normalized_ticket(normalized_root: Path, ticket_key: str):
    """Find ticket in normalized date folders, preferring latest date path."""
    matches = sorted(normalized_root.glob(f"*/{ticket_key}.json"))
    if not matches:
        raise SystemExit(
            f"Ticket {ticket_key} not found in normalized-tickets under {normalized_root}"
        )
    return matches[-1]


def infer_project_key(ticket_key: str, normalized_data: dict):
    """Infer project key from normalized ticket JSON and fall back to prefix."""
    project = (
        normalized_data.get("ticket", {})
        .get("project", {})
        .get("key", "")
        .strip()
    )
    if project:
        return project
    if "-" in ticket_key:
        return ticket_key.split("-", 1)[0]
    return ""


def _tokenize(text: str):
    """Tokenize text and remove common stop words."""
    tokens = re.findall(r"[A-Za-z0-9]{3,}", text.lower())
    return [token for token in tokens if token not in STOP_WORDS]


def build_rule_pattern(summary: str, reason: str, ticket_key: str):
    """Build a simple regex pattern from reason/summary tokens."""
    ordered_unique = []
    for token in _tokenize(f"{reason} {summary}"):
        if token not in ordered_unique:
            ordered_unique.append(token)

    if len(ordered_unique) >= 2:
        return f"{re.escape(ordered_unique[0])}.*{re.escape(ordered_unique[1])}"
    if ordered_unique:
        return re.escape(ordered_unique[0])
    return re.escape(ticket_key)


def load_rules_engine(path: Path):
    """Load existing rules file and validate schema."""
    if not path.is_file():
        raise SystemExit(f"Rules engine file not found: {path}")

    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise SystemExit(f"Rules engine CSV is empty or missing headers: {path}")
        missing = REQUIRED_RULE_COLUMNS - set(fieldnames)
        if missing:
            raise SystemExit(
                f"Rules engine CSV missing required columns: {sorted(missing)}"
            )
        return fieldnames, list(reader)


def next_rule_id(existing_rows):
    """Return next rule id in R### format."""
    max_id = 0
    for row in existing_rows:
        match = RULE_ID_RE.match((row.get("RuleID") or "").strip())
        if match:
            max_id = max(max_id, int(match.group(1)))
    return f"R{max_id + 1:03d}"


def append_rule(path: Path, fieldnames, rule_row: dict):
    """Append one rule row to CSV using existing header order."""
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writerow(rule_row)


def run_interactive(
    args,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[..., None] = print,
):
    """Run interactive rule creation flow."""
    ticket_key = prompt_required("Ticket key (e.g. HPC-123456): ", input_fn, print_fn).upper()
    validate_ticket_key(ticket_key)

    raw_ticket_path = args.ticket_json_dir / f"{ticket_key}.json"
    if not raw_ticket_path.is_file():
        raise SystemExit(f"Ticket {ticket_key} not found in tickets-json: {raw_ticket_path}")

    normalized_ticket_path = find_normalized_ticket(args.normalized_root, ticket_key)
    normalized = load_ticket_json(normalized_ticket_path, "normalized")
    summary = normalized.get("ticket", {}).get("summary", "")
    project_key = infer_project_key(ticket_key, normalized)

    reason = prompt_required("Why should a new rule be added? ", input_fn, print_fn)
    failure_category = prompt_required("Category of Issue: ", input_fn, print_fn)
    category = prompt_required("Category: ", input_fn, print_fn)

    match_field = input_fn(f"Match Field [{args.match_field_default}]: ").strip()
    if not match_field:
        match_field = args.match_field_default

    auto_pattern = build_rule_pattern(summary, reason, ticket_key)
    rule_pattern = input_fn(f"Rule Pattern [{auto_pattern}]: ").strip()
    if not rule_pattern:
        rule_pattern = auto_pattern

    fieldnames, existing_rows = load_rules_engine(args.rules_engine)
    rule_id = next_rule_id(existing_rows)

    rule_row = {column: "" for column in fieldnames}
    rule_row.update(
        {
            "Project Key": project_key,
            "RuleID": rule_id,
            "Rule Pattern": rule_pattern,
            "Match Field": match_field,
            "Failure Category": failure_category,
            "Category": category,
            "Priority": str(args.priority),
            "Confidence": str(args.confidence),
            "Created By": args.created_by,
            "Hit Count": str(args.hit_count),
        }
    )

    print_fn("\nProposed rule:")
    for key in (
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
    ):
        print_fn(f"  {key}: {rule_row.get(key, '')}")

    confirm = input_fn(
        f"\nAppend rule {rule_id} to {args.rules_engine}? [y/N]: "
    ).strip().lower()
    if confirm != "y":
        print_fn("Aborted: rule was not saved.")
        return 1

    append_rule(args.rules_engine, fieldnames, rule_row)
    print_fn(f"Rule {rule_id} appended to {args.rules_engine}")
    return 0


def main(
    argv=None,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[..., None] = print,
):
    """CLI entrypoint."""
    args = parse_args(argv)
    return run_interactive(args, input_fn=input_fn, print_fn=print_fn)


if __name__ == "__main__":
    raise SystemExit(main())
