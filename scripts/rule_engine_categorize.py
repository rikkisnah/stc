#!/usr/bin/env python3
"""
Categorize all normalized tickets using ONLY the rule engine (no LLM).

Usage:
    python3 scripts/rule_engine_categorize.py
    python3 scripts/rule_engine_categorize.py --tickets-dir scripts/normalized-tickets/2026-02-08
    python3 scripts/rule_engine_categorize.py --rule-engine scripts/trained-data/golden-rules-engine/rule-engine.csv
    python3 scripts/rule_engine_categorize.py --output-dir scripts/analysis
    python3 scripts/rule_engine_categorize.py --project HPC
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
JIRA_BROWSE_BASE = "https://jira-sd.mc1.oracleiaas.com/browse"
HUMAN_AUDIT_GUIDANCE = (
    "Before audit use pending-review or needs-review. "
    "After audit set correct or incorrect."
)

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
    p.add_argument("--project", choices=["DO", "HPC"], default=None,
                   help="Only evaluate rules for this project key. "
                        "If omitted, auto-detects from each ticket's project field.")
    p.add_argument("--resume", action="store_true",
                   help="Skip tickets already present in the output CSV")
    p.add_argument("-y", "--yes", action="store_true",
                   help="Skip overwrite confirmation when replacing output CSV")
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


def load_rules(path, project=None):
    """Load rule-engine.csv, return list of rule dicts sorted by priority (desc).

    If *project* is given (e.g. "DO"), only rules whose ``Project Key``
    matches are loaded.  When *project* is None all rules are loaded and
    filtering happens per-ticket in ``evaluate_ticket``.
    """
    rules = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if project and row.get("Project Key", "") != project:
                continue
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


def get_ticket_project(ticket_data):
    """Return the Jira project key from a normalized ticket (e.g. 'DO', 'HPC')."""
    return ticket_data.get("ticket", {}).get("project", {}).get("key", "")


def evaluate_ticket(ticket_data, rules, project_key=None):
    """
    Evaluate all rules against a ticket.

    *project_key* is the resolved project for this ticket.  When set, rules
    whose ``Project Key`` doesn't match are skipped.  When the caller already
    filtered rules at load-time (``--project`` flag) this can be ``None``.

    Returns (category_rules, meta_rules) — lists of matched rule dicts.
    """
    category_rules = []
    meta_rules = []

    for rule in rules:
        if rule["_re"] is None:
            continue
        if project_key and rule.get("Project Key", "") != project_key:
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


def categorize_ticket(ticket_data, rules, project_key=None):
    """Produce one output row dict for a ticket.

    *project_key* is passed through to ``evaluate_ticket`` so that only
    rules matching the ticket's project are considered.
    """
    ticket_info = ticket_data.get("ticket", {})
    status_info = ticket_data.get("status", {})

    ticket_key = ticket_info.get("key")
    ticket_id = ticket_key or "UNKNOWN"
    ticket_url = f"{JIRA_BROWSE_BASE}/{ticket_key}" if ticket_key else ""
    # Keep this field concise for spreadsheet readability: use Jira summary,
    # not full normalized description body.
    ticket_description = ticket_info.get("summary", "") or ticket_data.get("description", "")
    ticket_project = get_ticket_project(ticket_data)
    status = status_info.get("current", "")
    created = status_info.get("created", "")
    age = compute_age(created)
    # Trim created to date only
    created_date = created[:10] if created else ""

    category_rules, meta_rules = evaluate_ticket(
        ticket_data, rules, project_key=project_key,
    )

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
        "Project Key": ticket_project,
        "Ticket": ticket_id,
        "Ticket URL": ticket_url,
        "Ticket Description": ticket_description,
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
        "Human Audit Guidance": HUMAN_AUDIT_GUIDANCE,
        "Human Comments": "",
    }


OUTPUT_FIELDS = [
    "Project Key", "Ticket", "Ticket URL", "Ticket Description",
    "Status", "Created", "Age", "Runbook Present",
    "Category of Issue", "Category", "Rules Used",
    "Categorization Source", "LLM Confidence",
    "Human Audit for Accuracy", "Human Audit Guidance", "Human Comments",
]


def main():
    args = parse_args()
    tickets_dir = args.tickets_dir or find_latest_tickets_dir()
    rule_engine_path = args.rule_engine
    output_dir = args.output_dir

    print(f"Tickets dir : {tickets_dir}")
    print(f"Rule engine : {rule_engine_path}")
    print(f"Output dir  : {output_dir}")
    print(f"Project     : {args.project or 'auto-detect'}")

    if not tickets_dir.is_dir():
        sys.exit(f"Tickets directory not found: {tickets_dir}")
    if not rule_engine_path.is_file():
        sys.exit(f"Rule engine not found: {rule_engine_path}")

    os.makedirs(output_dir, exist_ok=True)

    project_filter = args.project
    rules = load_rules(rule_engine_path, project=project_filter)
    print(f"Loaded {len(rules)} rules"
          + (f" (project={project_filter})" if project_filter else " (all projects)"))

    # Collect all ticket JSONs
    ticket_files = sorted(tickets_dir.glob("*.json"))
    print(f"Found {len(ticket_files)} ticket files")

    if not ticket_files:
        print("Nothing to process.")
        return

    # Load already-done tickets if resuming
    output_csv = output_dir / "tickets-categorized.csv"
    if output_csv.is_file() and not args.resume:
        if args.yes:
            print(f"Overwriting existing output: {output_csv}")
        else:
            answer = input(
                f"Output CSV already exists at {output_csv}. Overwrite? [y/N] "
            ).strip().lower()
            if answer != "y":
                print("Aborted.")
                sys.exit(0)

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

        # When --project is set, rules are already filtered at load time
        # so no per-ticket filtering needed.  Otherwise auto-detect from ticket.
        per_ticket_project = None if project_filter else get_ticket_project(ticket_data)
        row = categorize_ticket(ticket_data, rules, project_key=per_ticket_project)
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
