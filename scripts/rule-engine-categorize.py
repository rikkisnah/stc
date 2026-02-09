#!/usr/bin/env python3
"""
Categorize all normalized tickets using ONLY the rule engine (no LLM).

Usage:
    python3 scripts/rule-engine-categorize.py
    python3 scripts/rule-engine-categorize.py --tickets-dir scripts/normalized-tickets/2026-02-08
    python3 scripts/rule-engine-categorize.py --rule-engine scripts/trained-data/golden-rules-engine/rule-engine.csv
    python3 scripts/rule-engine-categorize.py --output-dir scripts/analysis
"""
import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RULE_ENGINE = REPO_ROOT / "scripts" / "trained-data" / "golden-rules-engine" / "rule-engine.csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "scripts" / "analysis"

# Meta-rules only set Runbook Present; they don't count as categorization rules
META_RULE_FAILURE = "Runbook Present = TRUE"


def parse_args():
    p = argparse.ArgumentParser(description="Rule-engine-only ticket categorization")
    p.add_argument("--tickets-dir", type=Path, default=None,
                   help="Directory containing normalized ticket JSONs. "
                        "Defaults to the most recent date folder under scripts/normalized-tickets/.")
    p.add_argument("--rule-engine", type=Path, default=DEFAULT_RULE_ENGINE,
                   help="Path to rule-engine.csv")
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                   help="Output directory for tickets-categorized.csv")
    p.add_argument("--resume", action="store_true",
                   help="Skip tickets already present in the output CSV")
    return p.parse_args()


def find_latest_tickets_dir():
    """Pick the most recent date folder under scripts/normalized-tickets/."""
    base = REPO_ROOT / "scripts" / "normalized-tickets"
    if not base.is_dir():
        sys.exit(f"No normalized-tickets directory found at {base}")
    date_dirs = sorted(d for d in base.iterdir() if d.is_dir())
    if not date_dirs:
        sys.exit("No date folders found under scripts/normalized-tickets/")
    return date_dirs[-1]


def load_rules(path):
    """Load rule-engine.csv, return list of rule dicts sorted by priority (desc)."""
    rules = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["Priority"] = int(row["Priority"])
            row["Confidence"] = float(row["Confidence"])
            row["Hit Count"] = int(row["Hit Count"])
            # Pre-compile the regex pattern
            try:
                row["_re"] = re.compile(row["Rule Pattern"], re.IGNORECASE)
            except re.error as e:
                print(f"WARNING: Bad regex in {row['RuleID']}: {e}", file=sys.stderr)
                row["_re"] = None
            rules.append(row)
    rules.sort(key=lambda r: r["Priority"], reverse=True)
    return rules


def get_ticket_field_text(ticket, field_spec):
    """
    Build the search text from a field spec like 'summary+description' or 'labels'.
    Returns a single string to regex-match against.
    """
    fields = [f.strip() for f in field_spec.split("+")]
    parts = []
    for field in fields:
        if field == "summary":
            parts.append(ticket.get("ticket", {}).get("summary", ""))
        elif field == "description":
            parts.append(ticket.get("description", ""))
        elif field == "labels":
            labels = ticket.get("labels", [])
            parts.append(" ".join(labels))
        elif field == "comments":
            for c in ticket.get("comments", []):
                parts.append(c.get("body", ""))
    return "\n".join(parts)


def evaluate_ticket(ticket_data, rules):
    """
    Evaluate all rules against a ticket.
    Returns (category_rules, meta_rules) — lists of matched rule dicts.
    """
    category_rules = []
    meta_rules = []

    for rule in rules:
        if rule["_re"] is None:
            continue
        text = get_ticket_field_text(ticket_data, rule["Match Field"])
        if rule["_re"].search(text):
            if rule["Failure Category"] == META_RULE_FAILURE:
                meta_rules.append(rule)
            else:
                category_rules.append(rule)

    return category_rules, meta_rules


def compute_age(created_str):
    """Days since ticket creation."""
    try:
        created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - created
        return max(0, delta.days)
    except (ValueError, AttributeError):
        return ""


def categorize_ticket(ticket_data, rules):
    """Produce one output row dict for a ticket."""
    ticket_info = ticket_data.get("ticket", {})
    status_info = ticket_data.get("status", {})

    ticket_id = ticket_info.get("key", "UNKNOWN")
    status = status_info.get("current", "")
    created = status_info.get("created", "")
    age = compute_age(created)
    # Trim created to date only
    created_date = created[:10] if created else ""

    category_rules, meta_rules = evaluate_ticket(ticket_data, rules)

    runbook_present = "TRUE" if meta_rules else "FALSE"

    if category_rules:
        # Use highest-priority match (list is already sorted by priority desc)
        top_rule = category_rules[0]
        category_of_issue = top_rule["Failure Category"]
        category = top_rule["Category"]

        # Dynamic extraction from the summary for generic categories.
        summary = ticket_info.get("summary", "")

        # TRS: pull the specific TRS code (e.g. TRS_DIMM_REPLACEMENT).
        if category == "TRS":
            trs_match = re.search(r"TRS_\w+", summary, re.IGNORECASE)
            if trs_match:
                category = trs_match.group(0)

        # PRESCRIPTIVE: extract component after the action verb.
        # e.g. "[Prescriptive Action] Serial: 2551XK106X, RESEAT CHASSIS" → CHASSIS
        if category == "PRESCRIPTIVE":
            comp_match = re.search(
                r"Serial:\s*\S+,\s*\S+\s+(\S+)", summary, re.IGNORECASE,
            )
            if comp_match:
                category = comp_match.group(1).upper()
        rules_used = ",".join(r["RuleID"] for r in category_rules)
        source = "rule"
        confidence = max(r["Confidence"] for r in category_rules)
        audit = "needs-review" if confidence < 0.5 else "pending-review"
    else:
        category_of_issue = "uncategorized"
        category = "unknown"
        rules_used = ""
        source = "none"
        confidence = ""
        audit = "needs-review"

    return {
        "Ticket": ticket_id,
        "Status": status,
        "Created": created_date,
        "Age": age,
        "Runbook Present": runbook_present,
        "Category of Issue": category_of_issue,
        "Category": category,
        "Rules Used": rules_used,
        "Categorization Source": source,
        "LLM Confidence": confidence,
        "Human Audit for Accuracy": audit,
        "Human Comments": "",
    }


OUTPUT_FIELDS = [
    "Ticket", "Status", "Created", "Age", "Runbook Present",
    "Category of Issue", "Category", "Rules Used",
    "Categorization Source", "LLM Confidence",
    "Human Audit for Accuracy", "Human Comments",
]


def main():
    args = parse_args()
    tickets_dir = args.tickets_dir or find_latest_tickets_dir()
    rule_engine_path = args.rule_engine
    output_dir = args.output_dir

    print(f"Tickets dir : {tickets_dir}")
    print(f"Rule engine : {rule_engine_path}")
    print(f"Output dir  : {output_dir}")

    if not tickets_dir.is_dir():
        sys.exit(f"Tickets directory not found: {tickets_dir}")
    if not rule_engine_path.is_file():
        sys.exit(f"Rule engine not found: {rule_engine_path}")

    os.makedirs(output_dir, exist_ok=True)

    rules = load_rules(rule_engine_path)
    print(f"Loaded {len(rules)} rules")

    # Collect all ticket JSONs
    ticket_files = sorted(tickets_dir.glob("*.json"))
    print(f"Found {len(ticket_files)} ticket files")

    if not ticket_files:
        print("Nothing to process.")
        return

    # Load already-done tickets if resuming
    output_csv = output_dir / "tickets-categorized.csv"
    done_tickets = set()
    if args.resume and output_csv.is_file():
        with open(output_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                done_tickets.add(row["Ticket"])
        print(f"Resuming — {len(done_tickets)} tickets already processed")

    # Process
    results = []
    stats = {"rule": 0, "none": 0, "runbook": 0, "skipped": 0}

    for tf in ticket_files:
        ticket_id = tf.stem
        if ticket_id in done_tickets:
            stats["skipped"] += 1
            continue

        with open(tf, encoding="utf-8") as f:
            ticket_data = json.load(f)

        row = categorize_ticket(ticket_data, rules)
        results.append(row)

        if row["Categorization Source"] == "rule":
            stats["rule"] += 1
        else:
            stats["none"] += 1
        if row["Runbook Present"] == "TRUE":
            stats["runbook"] += 1

    # Write output
    write_header = not (args.resume and output_csv.is_file() and done_tickets)
    mode = "a" if (args.resume and output_csv.is_file() and done_tickets) else "w"

    with open(output_csv, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerows(results)

    total = len(results)
    print(f"\nDone. {total} tickets categorized → {output_csv}")
    print(f"  Rule matched : {stats['rule']}")
    print(f"  No match     : {stats['none']}")
    print(f"  Runbook=TRUE : {stats['runbook']}")
    if stats["skipped"]:
        print(f"  Skipped      : {stats['skipped']}")


if __name__ == "__main__":
    main()
