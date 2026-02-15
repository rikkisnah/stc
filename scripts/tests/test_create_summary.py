# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted
"""Tests for create_summary.py with 100% module coverage."""

import csv
import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "create_summary", SCRIPT_DIR / "create_summary.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


parse_args = mod.parse_args
load_ticket_rows = mod.load_ticket_rows
build_jql_query = mod.build_jql_query
summarize_by_category = mod.summarize_by_category
write_summary_csv = mod.write_summary_csv
main = mod.main
DEFAULT_OUTPUT_NAME = mod.DEFAULT_OUTPUT_NAME
DEFAULT_TICKETS_CSV = mod.DEFAULT_TICKETS_CSV


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


class TestParseArgs:
    def test_tickets_override_and_optional_output(self, tmp_path):
        tickets = tmp_path / "tickets.csv"
        out = tmp_path / "summary.csv"
        with patch.object(sys, "argv", ["create_summary.py", "--tickets", str(tickets), "--output", str(out)]):
            args = parse_args()

        assert args.tickets == tickets
        assert args.output == out

    def test_defaults_tickets_path_when_not_provided(self):
        with patch.object(sys, "argv", ["create_summary.py"]):
            args = parse_args()
        assert args.tickets == DEFAULT_TICKETS_CSV
        assert args.output is None


class TestLoadTicketRows:
    def test_loads_valid_rows(self, tmp_path):
        src = tmp_path / "tickets.csv"
        _write_csv(src, ["Ticket", "Category"], [["HPC-1", "Cable"]])

        rows = load_ticket_rows(src)

        assert rows == [{"Ticket": "HPC-1", "Category": "Cable"}]

    def test_raises_for_missing_columns(self, tmp_path):
        src = tmp_path / "tickets.csv"
        _write_csv(src, ["Ticket"], [["HPC-1"]])

        with pytest.raises(ValueError, match="Missing: Category"):
            load_ticket_rows(src)

    def test_raises_for_empty_file(self, tmp_path):
        src = tmp_path / "tickets.csv"
        src.write_text("", encoding="utf-8")

        with pytest.raises(ValueError, match="Missing: Category, Ticket"):
            load_ticket_rows(src)


class TestBuildJqlQuery:
    def test_returns_empty_for_no_keys(self):
        assert build_jql_query([]) == ""

    def test_builds_issuekey_query(self):
        assert build_jql_query(["HPC-1", "DO-2"]) == "issuekey in (HPC-1, DO-2)"


class TestSummarizeByCategory:
    def test_summarizes_and_deduplicates_keys(self):
        rows = [
            {"Ticket": "HPC-2", "Category": "Cable"},
            {"Ticket": "HPC-1", "Category": "Cable"},
            {"Ticket": "HPC-1", "Category": "Cable"},
            {"Ticket": "DO-5", "Category": "unknown"},
            {"Ticket": "", "Category": "NoKey"},
            {"Ticket": "DO-7", "Category": "  "},
        ]

        summary = summarize_by_category(rows)

        assert summary == [
            {
                "Tickets Category": "Cable",
                "Percentage of Total Tickets": "33.33%",
                "Count of Tickets": "2",
                "JQL Query": "issuekey in (HPC-1, HPC-2)",
            },
            {
                "Tickets Category": "unknown",
                "Percentage of Total Tickets": "33.33%",
                "Count of Tickets": "2",
                "JQL Query": "issuekey in (DO-5, DO-7)",
            },
        ]

    def test_handles_empty_rows(self):
        assert summarize_by_category([]) == []


class TestWriteSummaryCsv:
    def test_writes_output_and_creates_parent(self, tmp_path):
        out = tmp_path / "nested" / "tickets-summary.csv"
        rows = [
            {
                "Tickets Category": "Cable",
                "Percentage of Total Tickets": "100.00%",
                "Count of Tickets": "1",
                "JQL Query": "issuekey in (HPC-1)",
            }
        ]

        write_summary_csv(rows, out)

        with out.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            read_rows = list(reader)

        assert read_rows == rows


class TestMain:
    def test_main_happy_path_default_output(self, tmp_path, capsys):
        tickets = tmp_path / "tickets-categorized.csv"
        _write_csv(
            tickets,
            ["Ticket", "Category"],
            [["HPC-1", "Cable"], ["HPC-2", "Cable"], ["DO-1", "Power"]],
        )

        with patch.object(sys, "argv", ["create_summary.py", "--tickets", str(tickets)]):
            main()

        out = tickets.parent / DEFAULT_OUTPUT_NAME
        assert out.exists()
        output = capsys.readouterr().out
        assert "Input rows : 3" in output
        assert f"Output CSV : {out}" in output
        assert "Categories : 2" in output

    def test_main_exits_when_tickets_missing(self, tmp_path):
        missing = tmp_path / "missing.csv"

        with patch.object(sys, "argv", ["create_summary.py", "--tickets", str(missing)]):
            with pytest.raises(SystemExit, match=f"Tickets CSV not found: {missing}"):
                main()

    def test_main_exits_for_invalid_columns(self, tmp_path):
        bad = tmp_path / "bad.csv"
        _write_csv(bad, ["Ticket"], [["HPC-1"]])

        with patch.object(sys, "argv", ["create_summary.py", "--tickets", str(bad)]):
            with pytest.raises(SystemExit, match="Missing: Category"):
                main()
