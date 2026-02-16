#!/usr/bin/env python3
# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted
"""Keep AGENTS.md and CLAUDE.md synchronized.

Usage:
    python3 scripts/sync_agents_claude.py
    python3 scripts/sync_agents_claude.py --check
    python3 scripts/sync_agents_claude.py --source AGENTS.md --destination CLAUDE.md
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT / "AGENTS.md"
DEFAULT_DESTINATION = REPO_ROOT / "CLAUDE.md"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Sync AGENTS.md content into CLAUDE.md.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Source markdown file (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=DEFAULT_DESTINATION,
        help=f"Destination markdown file (default: {DEFAULT_DESTINATION})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check mode only: exit non-zero if files are out of sync.",
    )
    return parser.parse_args()


def files_match(source: Path, destination: Path) -> bool:
    """Return True when source and destination content are byte-identical."""
    if not destination.is_file():
        return False
    return source.read_bytes() == destination.read_bytes()


def sync_files(source: Path, destination: Path) -> bool:
    """Copy source to destination when content differs.

    Returns True when a write occurred.
    """
    source_bytes = source.read_bytes()
    if destination.is_file() and destination.read_bytes() == source_bytes:
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source_bytes)
    return True


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()

    if not args.source.is_file():
        sys.exit(f"Source file not found: {args.source}")

    if args.check:
        if files_match(args.source, args.destination):
            print(f"In sync: {args.source} == {args.destination}")
            return
        sys.exit(f"Out of sync: {args.source} != {args.destination}")

    changed = sync_files(args.source, args.destination)
    if changed:
        print(f"Updated {args.destination} from {args.source}")
    else:
        print(f"Already up to date: {args.destination}")


if __name__ == "__main__":
    main()
