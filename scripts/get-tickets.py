#!/usr/bin/env python3
"""Fetch tickets from Jira - Python version of get-tickets.sh"""

import argparse
import json
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests

DEFAULT_JIRA_TOKEN = "REDACTED_BITBUCKET_PAT"
BASE_URL = "https://jira-sd.mc1.oracleiaas.com"

BASE_JQL = """\
(labels = GPU_V6_E6-IS_MI355X_S.01 OR "Rack Type" = GPU_MI355X_E6_R.01)
AND status != "Pending Part(s)"
AND (("Region / Domain" IN (aga.ad1, "AGA5 (AD)")
      OR "Region Affected" = AGA
      OR "Canonical AD" = aga.ad1
      OR Building = aga5)
     AND ("Rack Type" IN (GPU_MI355X_E6_R.02, GPU_MI355X_E6_R.01)
          OR labels IN (GPU_V6_E6-IS_MI355X_S.02, GPU_V6_E6-IS_MI355X_S.01, AGA-CPV))
     AND summary !~ "Master")
AND project = "DC Ops"
AND issuetype != "Service Request"
AND "Component / Item" NOT IN cascadeOption(10046, 10064)"""

RESOLVED_FILTER = '\n     AND resolution = Resolved'
UNRESOLVED_FILTER = '\n     AND resolution = Unresolved'

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "tickets-json"
CONFIG_ENV_PATH = SCRIPT_DIR.parent / "env.json"


def load_jira_token():
    """Load Jira token from config.

    Precedence:
      1) env.json (repo root) with key "jira_token"
      2) DEFAULT_JIRA_TOKEN (legacy fallback)
    """

    try:
        text = CONFIG_ENV_PATH.read_text(encoding="utf-8")
        data = json.loads(text)
        token = data.get("jira_token")
        if token and token != "PLACEHOLDER":
            print(f"Using Jira token from {CONFIG_ENV_PATH}.")
            return token
        print(
            f"Warning: {CONFIG_ENV_PATH} missing/placeholder 'jira_token'; using default token.",
            file=sys.stdout,
        )
    except FileNotFoundError:
        print(
            f"Warning: {CONFIG_ENV_PATH} not found; using default token.",
            file=sys.stdout,
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"Warning: failed reading {CONFIG_ENV_PATH} ({exc}); using default token.",
            file=sys.stdout,
        )

    print("Using embedded Jira token.")
    return DEFAULT_JIRA_TOKEN


def make_headers():
    return {
        "Authorization": f"Bearer {load_jira_token()}",
        "Accept": "application/json",
    }


def parse_ticket_key(value):
    """Extract a ticket key from a key or browse URL."""
    m = re.search(r"/browse/([A-Z]+-\d+)$", value)
    if m:
        return m.group(1)
    if re.match(r"^[A-Z]+-\d+$", value):
        return value
    return None


def archive_existing(output_dir, force=False):
    """If output_dir exists and has .json files, archive it as a timestamped zip."""
    json_files = list(output_dir.glob("*.json"))
    if not json_files:
        return None

    print(f"Warning: {output_dir}/ contains {len(json_files)} existing JSON file(s).")
    if not force:
        answer = input("Archive and overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"tickets_json_{timestamp}"
    # Archive the specific output_dir passed in (often a temp dir in tests).
    archive_path = shutil.make_archive(
        str(output_dir.parent / archive_name),
        "zip",
        root_dir=str(output_dir.parent),
        base_dir=output_dir.name,
    )
    print(f"Archived existing tickets to {archive_path}")

    for f in json_files:
        f.unlink()

    return archive_path


def fetch_single_ticket(ticket_key):
    """Fetch a single ticket by its key."""
    print(f"Fetching ticket {ticket_key}...")
    url = f"{BASE_URL}/rest/api/2/issue/{ticket_key}"
    resp = requests.get(url, headers=make_headers())

    data = resp.json()

    errors = data.get("errorMessages")
    if errors:
        print(f"Error: {errors[0]}", file=sys.stderr)
        sys.exit(1)

    if "key" not in data:
        print("Error: Failed to parse response:", file=sys.stderr)
        print(json.dumps(data, indent=2)[:500], file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{ticket_key}.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(f"Done. Saved to {out_path}")


def load_jql_from_file(path):
    """Load JQL content from a file.

    Returns the stripped content if non-empty, otherwise None.
    """

    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Warning: failed reading JQL file {path} ({exc}); using BASE_JQL.")
        return None

    jql = text.strip()
    if not jql:
        print(f"Warning: JQL file {path} is empty; using BASE_JQL.")
        return None

    return jql


def fetch_search(date_filter="", force=False, include_unresolved=False,
                 unresolved_only=False, jql=None):
    """Fetch tickets via JQL search with optional date filter."""
    base_jql = jql if jql else BASE_JQL
    jql = base_jql
    if unresolved_only:
        jql += UNRESOLVED_FILTER
    elif not include_unresolved:
        jql += RESOLVED_FILTER
    jql += date_filter

    encoded_jql = quote(jql)
    print(f"JQL URL: {BASE_URL}/issues/?jql={encoded_jql}")
    print()

    archive_existing(OUTPUT_DIR, force=force)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    headers = make_headers()
    start_at = 0
    max_results = 100
    total_fetched = 0

    while True:
        print(f"Fetching tickets starting at {start_at}...")
        resp = requests.get(
            f"{BASE_URL}/rest/api/2/search",
            headers=headers,
            params={
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "*all,comment",
            },
        )

        data = resp.json()
        issues = data.get("issues")

        if issues is None:
            print("Error: Failed to parse response:", file=sys.stderr)
            print(json.dumps(data, indent=2)[:500], file=sys.stderr)
            sys.exit(1)

        count = len(issues)
        if count == 0:
            break

        total = data.get("total", "?")
        total_fetched += count
        print(f"  Got {count} tickets ({total_fetched}/{total} total)")

        out_path = OUTPUT_DIR / f"page_{start_at}.json"
        out_path.write_text(json.dumps(data, indent=2))

        start_at += max_results

    pages = start_at // max_results
    print(f"Done. Fetched {total_fetched} tickets across {pages} pages.")


def build_date_filter(args):
    """Build JQL date filter clause from parsed args."""
    if args.relative_days is not None:
        days = args.relative_days
        print(f"Filtering: tickets created in the last {days} day(s)")
        return f' AND created >= "-{days}d"'
    if args.start_date and args.end_date:
        print(f"Filtering: tickets created from {args.start_date} to {args.end_date}")
        return f' AND created >= "{args.start_date}" AND created <= "{args.end_date}"'
    if args.start_date:
        print(f"Filtering: tickets created from {args.start_date} to now")
        return f' AND created >= "{args.start_date}"'
    return ""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Fetch tickets from Jira",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s -a                           Fetch all tickets
  %(prog)s -a -2d                       Last 2 days
  %(prog)s -a 2025-01-01                From 2025-01-01 to now
  %(prog)s -a 2025-01-01 2025-01-31     Between two dates
  %(prog)s -t DO-2639750                Fetch single ticket
  %(prog)s -t https://jira-sd.mc1.oracleiaas.com/browse/DO-2639750
""",
    )
    parser.add_argument(
        "-a", "--all", action="store_true", dest="fetch_all",
        help="Fetch all matching tickets (with optional date filter)",
    )
    parser.add_argument(
        "--jql-file",
        help="Path to a file containing a custom JQL query (used with -a/--all)",
    )
    parser.add_argument(
        "--include-unresolved", action="store_true",
        help="Include unresolved tickets (default: only resolved)",
    )
    parser.add_argument(
        "--unresolved-only", action="store_true",
        help="Fetch only unresolved tickets",
    )
    parser.add_argument(
        "-y", "--yes", action="store_true",
        help="Skip confirmation prompt when overwriting existing tickets",
    )
    parser.add_argument(
        "-t", "--ticket",
        help="Fetch a single ticket by key (e.g. DO-2639750) or browse URL",
    )
    parser.add_argument(
        "positional", nargs="*", metavar="ARG",
        help="Relative days (-Nd), start date (YYYY-MM-DD), or start and end dates",
    )

    args, remaining = parser.parse_known_args(argv)

    # Merge remaining args (like -2d) into positional, excluding values that
    # belong to known flags (e.g. --jql-file PATH).
    positional = list(args.positional or [])
    skip_next = False
    for token in remaining:
        if skip_next:
            skip_next = False
            continue
        if token == "--jql-file":
            skip_next = True
            continue
        positional.append(token)

    # Parse positional args into structured fields
    args.relative_days = None
    args.start_date = None
    args.end_date = None

    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    rel_re = re.compile(r"^-(\d+)d$")
    if len(positional) == 1:
        m = rel_re.match(positional[0])
        if m:
            args.relative_days = int(m.group(1))
        elif date_re.match(positional[0]):
            args.start_date = positional[0]
        else:
            parser.error(f"Invalid argument: {positional[0]}")
    elif len(positional) == 2:
        if date_re.match(positional[0]) and date_re.match(positional[1]):
            args.start_date = positional[0]
            args.end_date = positional[1]
        else:
            parser.error("Date range must be YYYY-MM-DD YYYY-MM-DD")
    elif len(positional) > 2:
        parser.error("Too many arguments")

    # Enforce --jql-file usage
    if args.jql_file and not args.fetch_all:
        parser.error("--jql-file requires -a/--all")

    # Show help if no action specified
    if not args.fetch_all and not args.ticket:
        parser.print_help()
        sys.exit(0)

    return args


def main(argv=None):
    start_time = time.monotonic()
    args = parse_args(argv)

    if args.ticket:
        ticket_key = parse_ticket_key(args.ticket)
        if not ticket_key:
            print(f"Error: Invalid ticket key or URL: {args.ticket}", file=sys.stderr)
            sys.exit(1)
        fetch_single_ticket(ticket_key)
    elif args.fetch_all:
        date_filter = build_date_filter(args)
        custom_jql = load_jql_from_file(args.jql_file) if args.jql_file else None
        fetch_search(
            date_filter,
            force=args.yes,
            include_unresolved=args.include_unresolved,
            unresolved_only=args.unresolved_only,
            jql=custom_jql,
        )

    elapsed = time.monotonic() - start_time
    print(f"\nCompleted in {elapsed:.2f}s.")


if __name__ == "__main__":
    main()
