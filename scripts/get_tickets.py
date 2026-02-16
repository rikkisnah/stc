#!/usr/bin/env python3
"""Fetch tickets from Jira - Python version of get_tickets.sh.

Supports limiting output with `--number-of-tickets` to capture the first N
tickets (written to `--output-file`, defaulting to
`scripts/tickets-json/limited-tickets.json`).
"""

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

REQUEST_TIMEOUT_SECONDS = 45
REQUEST_RETRY_COUNT = 3
REQUEST_RETRY_DELAY_SECONDS = 2

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


def _request_json(url, *, headers=None, params=None, context="Jira request"):
    """Run a GET request with timeout + retry and return the JSON body.

    Raises SystemExit on repeated request failures so callers get a clear
    error instead of waiting indefinitely.
    """

    for attempt in range(1, REQUEST_RETRY_COUNT + 1):
        try:
            resp = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.Timeout:
            print(
                f"Warning: {context} timed out (attempt {attempt}/{REQUEST_RETRY_COUNT}).",
                file=sys.stderr,
            )
        except requests.RequestException as exc:
            print(
                f"Warning: {context} failed (attempt {attempt}/{REQUEST_RETRY_COUNT}): {exc}",
                file=sys.stderr,
            )
        if attempt < REQUEST_RETRY_COUNT:
            time.sleep(REQUEST_RETRY_DELAY_SECONDS)

    print(
        f"Error: {context} failed after {REQUEST_RETRY_COUNT} attempt(s); aborting.",
        file=sys.stderr,
    )
    sys.exit(1)


def parse_ticket_key(value):
    """Extract a ticket key from a key or browse URL."""
    m = re.search(r"/browse/([A-Z]+-\d+)$", value)
    if m:
        return m.group(1)
    if re.match(r"^[A-Z]+-\d+$", value):
        return value
    return None


def load_tickets_file(path):
    """Load ticket keys from a text file, one per line.

    Skips blank lines and lines starting with ``#``.  Each non-comment
    line is parsed via :func:`parse_ticket_key` (accepts both plain keys
    and browse URLs).  Duplicates are removed while preserving first-seen
    order.

    Returns a list of validated, unique ticket keys.
    Raises ``SystemExit`` if the file cannot be read, is empty after
    filtering, or contains lines that are not valid ticket keys/URLs.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Error: cannot read tickets file {path}: {exc}", file=sys.stderr)
        sys.exit(1)

    seen = {}
    invalid = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key = parse_ticket_key(line)
        if key is None:
            invalid.append(line)
        elif key not in seen:
            seen[key] = True

    if invalid:
        print(f"Error: invalid ticket key(s) in {path}:", file=sys.stderr)
        for bad in invalid:
            print(f"  {bad}", file=sys.stderr)
        sys.exit(1)

    if not seen:
        print(f"Error: no ticket keys found in {path}", file=sys.stderr)
        sys.exit(1)

    return list(seen.keys())


def fetch_tickets_from_file(file_path, force=False):
    """Fetch multiple tickets listed in a text file.

    Reads ticket keys via :func:`load_tickets_file`, archives existing
    output in ``OUTPUT_DIR`` (prompting unless *force* is True), then
    fetches each ticket individually.
    """
    keys = load_tickets_file(file_path)
    print(f"Loaded {len(keys)} unique ticket(s) from {file_path}")

    archive_existing(OUTPUT_DIR, force=force)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for key in keys:
        fetch_single_ticket(key)

    print(f"Fetched {len(keys)} ticket(s) from file.")


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
    data = _request_json(url, headers=make_headers(), context=f"fetch_single_ticket {ticket_key}")

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
                 unresolved_only=False, include_resolved_only=False, jql=None, number_of_tickets=None,
                 output_file=None):
    """Fetch tickets via JQL search with optional date filter.

    When ``number_of_tickets`` is provided, only the first N tickets are
    collected and written to ``output_file`` instead of paging to
    ``scripts/tickets-json/``.
    """

    base_jql = jql if jql else BASE_JQL
    jql = base_jql
    if unresolved_only:
        jql += UNRESOLVED_FILTER
    elif include_resolved_only:
        jql += RESOLVED_FILTER
    elif not include_unresolved:
        jql += RESOLVED_FILTER
    jql += date_filter

    encoded_jql = quote(jql)
    print(f"JQL URL: {BASE_URL}/issues/?jql={encoded_jql}")
    print()

    limited_mode = number_of_tickets is not None
    remaining = number_of_tickets
    limited_issues = []

    if limited_mode:
        if not output_file:
            raise ValueError("output_file is required when limiting tickets")
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        archive_existing(OUTPUT_DIR, force=force)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    headers = make_headers()
    start_at = 0
    max_results = min(remaining, 100) if limited_mode else 100
    total_fetched = 0
    pages = 0
    reported_total = None

    while True:
        print(f"Fetching tickets starting at {start_at}...")
        data = _request_json(
            f"{BASE_URL}/rest/api/2/search",
            headers=headers,
            params={
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "*all,comment",
            },
            context=f"fetch_search startAt={start_at} maxResults={max_results}",
        )
        issues = data.get("issues")

        if issues is None:
            print("Error: Failed to parse response:", file=sys.stderr)
            print(json.dumps(data, indent=2)[:500], file=sys.stderr)
            sys.exit(1)

        count = len(issues)
        if count == 0:
            break

        total = data.get("total", "?")
        if reported_total is None and total not in (None, "?"):
            reported_total = total

        if limited_mode:
            to_take = issues if remaining is None else issues[:remaining]
            limited_issues.extend(to_take)
            taken_count = len(to_take)
            total_fetched += taken_count
            if remaining is not None:
                remaining -= taken_count
            print(f"  Got {taken_count} tickets ({total_fetched}/{number_of_tickets} requested)")

            if remaining is not None and remaining <= 0:
                break

            start_at += count
            max_results = min(remaining, 100) if remaining is not None else 100
            pages += 1
            # Continue fetching until Jira returns 0 issues.
            continue

        total_fetched += count
        print(f"  Got {count} tickets ({total_fetched}/{total} total)")

        out_path = OUTPUT_DIR / f"page_{start_at}.json"
        out_path.write_text(json.dumps(data, indent=2))

        start_at += max_results
        pages += 1

    if limited_mode:
        payload = {
            "issues": limited_issues,
            "total": reported_total if reported_total is not None else len(limited_issues),
            "fetched": len(limited_issues),
            "limited": True,
        }
        output_path.write_text(json.dumps(payload, indent=2))
        print(f"Done. Fetched {len(limited_issues)} ticket(s); wrote subset to {output_path}.")
    else:
        pages = pages or (start_at // max_results if max_results else 0)
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


def _extract_positional_tokens(argv_list):
    """Return positional-like tokens in their original order."""

    # Map of recognized flags to the number of value tokens they consume.
    option_arg_counts = {
        "-a": 0,
        "--all": 0,
        "--include-unresolved": 0,
        "--include-resolved-only": 0,
        "--unresolved-only": 0,
        "-y": 0,
        "--yes": 0,
        "-t": 1,
        "--ticket": 1,
        "--jql-file": 1,
        "-f": 1,
        "--tickets-file": 1,
        "--number-of-tickets": 1,
        "--output-file": 1,
        "-h": 0,
        "--help": 0,
    }

    positional = []
    i = 0
    treat_all_as_positional = False

    while i < len(argv_list):
        token = argv_list[i]

        if treat_all_as_positional:
            positional.append(token)
            i += 1
            continue

        if token == "--":
            treat_all_as_positional = True
            i += 1
            continue

        option_arity = option_arg_counts.get(token)
        if option_arity is not None:
            i += 1 + option_arity
            continue

        if token.startswith("--") and "=" in token:
            option_name, _ = token.split("=", 1)
            option_arity = option_arg_counts.get(option_name)
            if option_arity is not None:
                i += 1
                continue

        positional.append(token)
        i += 1

    return positional


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Fetch tickets from Jira.\n\n"
            "Modes:\n"
            "  -a/--all          Bulk JQL search mode (required for --jql-file, date filters, and --number-of-tickets)\n"
            "  -t/--ticket       Single-ticket mode\n"
            "  -f/--tickets-file Ticket-list mode (one key per line)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s -a                           Fetch all tickets
  %(prog)s -a -2d                       Last 2 days
  %(prog)s -a 2025-01-01                From 2025-01-01 to now
  %(prog)s -a 2025-01-01 2025-01-31     Between two dates
  %(prog)s -t DO-2639750                Fetch single ticket
  %(prog)s -t https://jira-sd.mc1.oracleiaas.com/browse/DO-2639750
  %(prog)s -f tickets.txt                Fetch tickets listed in file
  %(prog)s -f tickets.txt -y             Fetch from file, skip archive prompt
""",
    )
    parser.add_argument(
        "-a", "--all", action="store_true", dest="fetch_all",
        help="Bulk JQL search mode; required for --jql-file, date filters, and --number-of-tickets",
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
        "--include-resolved-only", action="store_true",
        help="Fetch only resolved tickets (explicit mode)",
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
        "-f", "--tickets-file",
        help="Path to a text file with ticket keys (one per line); "
             "lines starting with '#' and blank lines are skipped",
    )
    parser.add_argument(
        "--number-of-tickets", type=int,
        help="Fetch only the first N tickets and write them to a single file",
    )
    parser.add_argument(
        "--output-file",
        help="Path to save the limited ticket batch (requires --number-of-tickets)",
    )
    parser.add_argument(
        "positional", nargs="*", metavar="ARG",
        help="Relative days (-Nd), start date (YYYY-MM-DD), or start and end dates",
    )

    if argv is None:
        argv_list = sys.argv[1:]
    else:
        argv_list = list(argv)

    args, _ = parser.parse_known_args(argv_list)

    positional = _extract_positional_tokens(argv_list)

    # Enforce --jql-file usage
    if args.jql_file and not args.fetch_all:
        parser.error("--jql-file requires -a/--all")

    # Enforce --tickets-file mutual exclusion
    if args.tickets_file and args.ticket:
        parser.error("--tickets-file and --ticket are mutually exclusive")
    if args.tickets_file and args.fetch_all:
        parser.error("--tickets-file and --all are mutually exclusive")
    if args.include_unresolved and args.unresolved_only:
        parser.error("--include-unresolved and --unresolved-only are mutually exclusive")
    if args.include_resolved_only and args.include_unresolved:
        parser.error("--include-resolved-only and --include-unresolved are mutually exclusive")
    if args.include_resolved_only and args.unresolved_only:
        parser.error("--include-resolved-only and --unresolved-only are mutually exclusive")

    if args.number_of_tickets is not None:
        if not args.fetch_all:
            parser.error("--number-of-tickets requires -a/--all")
        if args.number_of_tickets <= 0:
            parser.error("--number-of-tickets must be a positive integer")
        if args.output_file is None:
            args.output_file = str(OUTPUT_DIR / "limited-tickets.json")
    else:
        if args.output_file is not None:
            parser.error("--output-file requires --number-of-tickets")

    # Parse positional args into structured fields.
    #
    # Prefer the *last-specified* date filter when multiple are provided.
    # Examples:
    #   -a -1d 2026-01-01 2026-01-02  -> uses 2026-01-01..2026-01-02
    #   -a 2026-01-01 2026-01-02 -1d  -> uses -1d
    args.relative_days = None
    args.start_date = None
    args.end_date = None

    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    rel_re = re.compile(r"^-(\d+)d$")

    selected = None
    last_range = None
    last_start = None
    last_rel = None
    invalid = []
    i = 0
    while i < len(positional):
        token = positional[i]
        m_rel = rel_re.match(token)
        if m_rel:
            last_rel = int(m_rel.group(1))
            selected = ("relative_days", last_rel)
            i += 1
            continue

        if date_re.match(token):
            # Potentially a range; if next token is also a date, treat as a range.
            if i + 1 < len(positional) and date_re.match(positional[i + 1]):
                last_range = (token, positional[i + 1])
                selected = ("date_range", last_range[0], last_range[1])
                i += 2
                continue
            last_start = token
            selected = ("start_date", last_start)

        else:
            invalid.append(token)

        i += 1

    # If we only have a partial date range (i.e. a start date plus junk), keep
    # previous strict behavior.
    if last_start is not None and last_range is None and invalid:
        parser.error("Date range must be YYYY-MM-DD YYYY-MM-DD")

    # If we have a valid date/relative filter, ignore other stray tokens.
    if invalid and selected is None:
        parser.error(f"Invalid argument(s): {' '.join(invalid)}")

    if selected is None:
        # Preserve previous behavior: allow no positional tokens, otherwise error.
        # If no action specified, behave like the old script and show help.
        if not args.fetch_all and not args.ticket and not args.tickets_file:
            parser.print_help()
            sys.exit(0)
        return args

    # Apply selected filter.
    #
    # Rules:
    # - If a date range appears anywhere, it wins over earlier -Nd.
    # - If -Nd appears after the last range, -Nd wins.
    if last_range is not None and last_rel is not None:
        # Determine whether the last seen filter was -Nd.
        if selected[0] == "relative_days":
            args.relative_days = last_rel
        else:
            args.start_date, args.end_date = last_range
    elif last_range is not None:
        args.start_date, args.end_date = last_range
    elif last_start is not None:
        args.start_date = last_start
    elif last_rel is not None:
        args.relative_days = last_rel

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
    elif args.tickets_file:
        fetch_tickets_from_file(args.tickets_file, force=args.yes)
    elif args.fetch_all:
        date_filter = build_date_filter(args)
        custom_jql = load_jql_from_file(args.jql_file) if args.jql_file else None
        fetch_search(
            date_filter,
            force=args.yes,
            include_unresolved=args.include_unresolved,
            unresolved_only=args.unresolved_only,
            include_resolved_only=args.include_resolved_only,
            jql=custom_jql,
            number_of_tickets=args.number_of_tickets,
            output_file=args.output_file,
        )

    elapsed = time.monotonic() - start_time
    print(f"\nCompleted in {elapsed:.2f}s.")


if __name__ == "__main__":
    main()
