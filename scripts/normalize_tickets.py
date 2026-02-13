#!/usr/bin/env python3
"""Normalize Jira ticket JSON files into a structured schema for LLM token efficiency.

Transforms raw Jira JSON into sections:
  ticket, status, people, location, labels, links, sla, description, comments

Filters out noise labels, automated bot comments, and API metadata.
"""

import argparse
import json
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = SCRIPT_DIR / "tickets-json"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "normalized-tickets"

# Label prefixes to remove (redundant with location/metadata fields)
NOISE_LABEL_PREFIXES = (
    "building:", "owner:", "pd:", "RackSerial:", "Realm:",
    "Region:", "TPEC-", "SPGXTAIL-",
)

# Exact labels to remove
NOISE_LABELS = frozenset({"ORTANO", "RegionChanged", "TPEC_UPDATED", "TRS_CUT"})

# Comment body prefixes that indicate noise
NOISE_COMMENT_PREFIXES = (
    "Ocean Notification sent to:",
    "Updated Jira Status",
)

# Comment author username prefixes for bots
NOISE_COMMENT_AUTHORS = (
    "jirasd-gear-rcp-autocut",
)


def trim_date(date_str):
    """Convert '2026-02-06T00:02:39.586+0000' to '2026-02-06T00:02:39Z'."""
    if not date_str:
        return None
    m = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", date_str)
    if m:
        return m.group(1) + "Z"
    return date_str


def clean_jira_text(text):
    """Clean Jira wiki markup and unicode artifacts, keeping content."""
    if not text:
        return None
    text = text.replace("\r\n", "\n")

    # Unicode cleanup
    text = text.replace("\u00a0", " ")        # non-breaking space
    text = text.replace("\ufffd", "")          # replacement character
    text = text.replace("\u2013", "-")         # en dash
    text = text.replace("\u2026", "...")        # ellipsis

    # Remove tqdm progress bar block chars (U+2580-U+259F range)
    text = re.sub(r"[\u2580-\u259f]+", "", text)

    # Jira formatting tags — strip markup, keep inner content
    text = re.sub(r"\{color(?::[^}]*)?\}", "", text)
    text = re.sub(r"\{code(?::[^}]*)?\}", "\n", text)
    text = re.sub(r"\{noformat\}", "\n", text)
    text = re.sub(r"\{panel(?::[^}]*)?\}", "\n", text)
    text = re.sub(r"\{\*\}", "", text)         # empty bold marker

    # Jira links: [display text|url] → display text
    text = re.sub(r"\[([^|\]]+)\|[^\]]+\]", r"\1", text)

    # Image references: !filename.png! → (remove)
    text = re.sub(r"![^!\s]+!", "", text)

    # Headings: h1. through h6. at start of line
    text = re.sub(r"^h[1-6]\.\s*", "", text, flags=re.MULTILINE)

    # Horizontal rules
    text = re.sub(r"^-{4,}\s*$", "", text, flags=re.MULTILINE)

    # Forced line breaks
    text = text.replace("\\\\", "\n")

    # Jira key-value table rows: |*Key*|Value| → Key: Value
    text = re.sub(r"\|\*([^*|]+)\*\|([^|\n]*)\|", r"\1: \2", text)

    # Table header/cell separators left over
    text = re.sub(r"\|\|", " | ", text)

    # Bold/italic markers around text (keep text)
    text = re.sub(r"\*\|", " ", text)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip trailing whitespace per line and overall
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = text.strip()

    return text if text else None


def extract_option_value(field):
    """Extract value from a Jira option object or list of option objects."""
    if isinstance(field, dict) and "value" in field:
        return field["value"]
    if isinstance(field, list):
        values = [
            item.get("value", item) if isinstance(item, dict) else item
            for item in field
        ]
        return values[0] if len(values) == 1 else values
    return field


def extract_ticket(issue):
    """Extract ticket identification section."""
    fields = issue.get("fields", {})
    project = fields.get("project", {})
    issuetype = fields.get("issuetype", {})
    priority = fields.get("priority", {})
    return {
        "id": issue.get("id"),
        "key": issue.get("key"),
        "project": {"key": project.get("key"), "name": project.get("name")},
        "type": issuetype.get("name"),
        "summary": (fields.get("summary") or "").strip(),
        "priority": priority.get("name"),
    }


def extract_status(fields):
    """Extract status section."""
    status = fields.get("status") or {}
    resolution = fields.get("resolution")
    return {
        "current": status.get("name"),
        "resolution": resolution.get("name") if resolution else None,
        "created": trim_date(fields.get("created")),
        "resolved": trim_date(fields.get("resolutiondate")),
        "updated": trim_date(fields.get("updated")),
    }


def extract_people(fields):
    """Extract people section."""
    assignee = fields.get("assignee")
    reporter = fields.get("reporter")
    watches = fields.get("watches")
    return {
        "assignee": assignee.get("displayName") if assignee else None,
        "reporter": reporter.get("displayName") if reporter else None,
        "watchers": watches.get("watchCount") if watches else None,
    }


def extract_rack_serial(labels):
    """Extract rack serial from RackSerial: label."""
    for label in labels:
        if label.startswith("RackSerial:"):
            return label.split(":", 1)[1]
    return None


def extract_location(fields):
    """Extract location section from custom fields."""
    return {
        "region": extract_option_value(fields.get("customfield_14606")),
        "availability_domain": extract_option_value(fields.get("customfield_12605")),
        "building": extract_option_value(fields.get("customfield_12604")),
        "rack_type": fields.get("customfield_10602"),
        "host_serial": fields.get("customfield_10104"),
        "rack_serial": extract_rack_serial(fields.get("labels", [])),
    }


def filter_labels(labels):
    """Filter out noise labels that are redundant with other fields."""
    result = []
    for label in labels:
        if label in NOISE_LABELS:
            continue
        if any(label.startswith(prefix) for prefix in NOISE_LABEL_PREFIXES):
            continue
        result.append(label)
    return result


def extract_links(fields):
    """Extract simplified issue links."""
    links = []
    for link in fields.get("issuelinks", []):
        link_type = link.get("type", {})

        if "outwardIssue" in link:
            issue = link["outwardIssue"]
            relation = link_type.get("outward", link_type.get("name", ""))
        elif "inwardIssue" in link:
            issue = link["inwardIssue"]
            relation = link_type.get("inward", link_type.get("name", ""))
        else:
            continue

        issue_fields = issue.get("fields", {})
        status = issue_fields.get("status", {})

        links.append({
            "key": issue.get("key"),
            "relation": relation,
            "status": status.get("name"),
            "summary": issue_fields.get("summary"),
        })
    return links


def extract_sla(fields):
    """Extract SLA elapsed times from completed or ongoing cycles."""
    def get_elapsed(sla_field):
        if not sla_field or not isinstance(sla_field, dict):
            return None
        cycles = sla_field.get("completedCycles", [])
        if cycles:
            return cycles[0].get("elapsedTime", {}).get("friendly")
        ongoing = sla_field.get("ongoingCycle")
        if ongoing:
            return ongoing.get("elapsedTime", {}).get("friendly")
        return None

    first_response = get_elapsed(fields.get("customfield_10003"))
    resolve_time = get_elapsed(fields.get("customfield_14710"))

    result = {}
    if first_response:
        result["time_to_first_response"] = first_response
    if resolve_time:
        result["time_to_resolve"] = resolve_time
    return result or None


def is_noise_comment(comment):
    """Check if a comment is automated noise that should be filtered out."""
    body = comment.get("body", "")
    author = comment.get("author", {})
    author_name = author.get("name", "") if isinstance(author, dict) else ""

    for prefix in NOISE_COMMENT_PREFIXES:
        if body.startswith(prefix):
            return True

    for prefix in NOISE_COMMENT_AUTHORS:
        if author_name.startswith(prefix):
            return True

    return False


def extract_comments(fields):
    """Extract and filter comments, removing automated noise."""
    comment_field = fields.get("comment", {})

    # Handle raw format (dict with comments key) or already-flattened (list)
    if isinstance(comment_field, dict):
        comments = comment_field.get("comments", [])
    elif isinstance(comment_field, list):
        comments = comment_field
    else:
        comments = []

    result = []
    for c in comments:
        if is_noise_comment(c):
            continue

        author = c.get("author", {})
        if isinstance(author, dict):
            author_name = author.get("displayName") or author.get("name", "unknown")
        else:
            author_name = str(author)

        result.append({
            "id": c.get("id"),
            "author": author_name,
            "created": trim_date(c.get("created")),
            "body": clean_jira_text(c.get("body")) or "",
        })
    return result


def normalize_issue(issue):
    """Normalize a single issue into the structured schema."""
    fields = issue.get("fields", {})

    result = {
        "ticket": extract_ticket(issue),
        "status": extract_status(fields),
        "people": extract_people(fields),
        "location": extract_location(fields),
        "labels": filter_labels(fields.get("labels", [])),
    }

    links = extract_links(fields)
    if links:
        result["links"] = links

    sla = extract_sla(fields)
    if sla:
        result["sla"] = sla

    description = clean_jira_text(fields.get("description"))
    if description:
        result["description"] = description

    result["comments"] = extract_comments(fields)

    return result


def normalize_json(data):
    """Normalize ticket JSON - handles both single tickets and paginated search results."""
    if "issues" in data:
        data["issues"] = [normalize_issue(issue) for issue in data["issues"]]
        for key in ("expand", "startAt", "maxResults"):
            data.pop(key, None)
    elif "fields" in data:
        data = normalize_issue(data)
    return data


def process_file(path, in_place=False, output_dir=None):
    """Process a single JSON file.

    For paginated search results (containing multiple issues), each ticket is
    written as a separate file named by its key (e.g. DO-2639750.json).

    Returns list of (out_path, original_size, normalized_size) tuples.
    """
    text = Path(path).read_text()
    original_size = len(text)
    data = json.loads(text)

    results = []

    if "issues" in data and not in_place:
        # Paginated search result — split into individual ticket files
        for issue in data["issues"]:
            normalized = normalize_issue(issue)
            output = json.dumps(normalized, indent=2)
            ticket_key = normalized.get("ticket", {}).get("key", "unknown")
            if output_dir:
                out_path = Path(output_dir) / f"{ticket_key}.json"
            else:
                out_path = Path(path).parent / f"{ticket_key}.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output)
            results.append((str(out_path), original_size, len(output)))
        # Use full original size only for the first entry; rest get 0
        # to avoid double-counting in totals
        for i in range(1, len(results)):
            results[i] = (results[i][0], 0, results[i][2])
    else:
        normalized = normalize_json(data)
        output = json.dumps(normalized, indent=2)
        normalized_size = len(output)

        if in_place:
            out_path = Path(path)
        elif output_dir:
            out_path = Path(output_dir) / Path(path).name
        else:
            out_path = Path(path)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output)
        results.append((str(out_path), original_size, normalized_size))

    return results


def archive_existing(output_dir, force=False):
    """If output_dir has .json files, archive them as a timestamped zip."""
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
    archive_name = f"{output_dir.name}_{timestamp}"
    archive_path = shutil.make_archive(
        str(SCRIPT_DIR / archive_name), "zip",
        root_dir=str(output_dir.parent), base_dir=output_dir.name,
    )
    print(f"Archived existing files to {archive_path}")

    for f in json_files:
        f.unlink()

    return archive_path


def load_tickets_file(path):
    """Load ticket keys from a text file for filtering.

    Skips blank lines and lines starting with ``#``.  Validates each
    line against the ``PROJ-NNNNN`` ticket key format or a Jira browse
    URL.  Duplicates are removed.

    Returns a set of validated ticket key strings.
    Raises ``SystemExit`` on read errors or invalid/empty content.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Error: cannot read tickets file {path}: {exc}", file=sys.stderr)
        sys.exit(1)

    seen = set()
    invalid = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Accept plain key or browse URL
        m = re.search(r"/browse/([A-Z]+-\d+)$", line)
        if m:
            seen.add(m.group(1))
        elif re.match(r"^[A-Z]+-\d+$", line):
            seen.add(line)
        else:
            invalid.append(line)

    if invalid:
        print(f"Error: invalid ticket key(s) in {path}:", file=sys.stderr)
        for bad in invalid:
            print(f"  {bad}", file=sys.stderr)
        sys.exit(1)

    if not seen:
        print(f"Error: no ticket keys found in {path}", file=sys.stderr)
        sys.exit(1)

    return seen


def main(argv=None):
    start_time = time.monotonic()
    parser = argparse.ArgumentParser(
        description="Normalize Jira ticket JSON files into a structured schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s                                         Normalize tickets-json/*.json -> normalized-tickets/
  %(prog)s -o output/                              Custom output directory
  %(prog)s tickets-json/DO-2639750.json            Normalize specific file(s)
  %(prog)s --in-place tickets-json/*.json          Normalize files in place
  %(prog)s -y                                       Skip overwrite confirmation
""",
    )
    parser.add_argument(
        "files", nargs="*", metavar="FILE",
        help="JSON files to normalize (default: tickets-json/*.json)",
    )
    parser.add_argument(
        "-o", "--output-dir",
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--date",
        help="Override output subdirectory date stamp (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--in-place", action="store_true",
        help="Normalize files in place instead of writing to output directory",
    )
    parser.add_argument(
        "-y", "--yes", action="store_true",
        help="Skip confirmation prompt when overwriting existing files",
    )
    parser.add_argument(
        "--tickets-file",
        help="Path to a text file with ticket keys; only matching "
             "tickets will be normalized (one key per line, '#' comments allowed)",
    )

    args = parser.parse_args(argv)

    # Default input: tickets-json/*.json
    files = args.files
    if not files:
        files = sorted(str(f) for f in DEFAULT_INPUT_DIR.glob("*.json"))
        if not files:
            print(f"No JSON files found in {DEFAULT_INPUT_DIR}/", file=sys.stderr)
            sys.exit(1)
        print(f"Input: {DEFAULT_INPUT_DIR}/ ({len(files)} file(s))")

    # Filter to specific tickets when --tickets-file is provided
    if args.tickets_file:
        ticket_keys = load_tickets_file(args.tickets_file)
        files = [f for f in files if Path(f).stem in ticket_keys]
        if not files:
            print(f"No JSON files match ticket keys from {args.tickets_file}",
                  file=sys.stderr)
            sys.exit(1)
        print(f"Filtered to {len(files)} file(s) matching "
              f"{len(ticket_keys)} ticket key(s)")

    # Determine output mode
    if args.in_place:
        output_dir = None
    else:
        base_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
        if args.date:
            try:
                datetime.strptime(args.date, "%Y-%m-%d")
            except ValueError as exc:
                parser.error("--date must be in YYYY-MM-DD format")
            date_stamp = args.date
        else:
            date_stamp = datetime.now().strftime("%Y-%m-%d")
        output_dir = base_dir / date_stamp
        output_dir.mkdir(parents=True, exist_ok=True)
        archive_existing(output_dir, force=args.yes)
        print(f"Output: {output_dir}/")

    print()

    total_original = 0
    total_normalized = 0
    total_tickets = 0

    for filepath in files:
        file_results = process_file(
            filepath,
            in_place=args.in_place,
            output_dir=str(output_dir) if output_dir else None,
        )
        for out_path, orig, norm in file_results:
            total_original += orig
            total_normalized += norm
            total_tickets += 1
            if orig:
                reduction = 100 - (norm * 100 // orig) if orig else 0
                print(f"  {filepath} -> {out_path} ({orig:,} -> {norm:,} chars, -{reduction}%)")
            else:
                print(f"  -> {out_path} ({norm:,} chars)")

    total_reduction = 100 - (total_normalized * 100 // total_original) if total_original else 0
    elapsed = time.monotonic() - start_time
    print(f"\nDone. {total_tickets} ticket(s), {total_original:,} -> {total_normalized:,} chars total (-{total_reduction}%). Took {elapsed:.2f}s.")


if __name__ == "__main__":
    main()
