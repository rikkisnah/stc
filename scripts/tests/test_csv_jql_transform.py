"""Tests for csv_jql_transform.py — 100% coverage target."""

import csv
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the hyphenated module via importlib
SCRIPT_DIR = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "csv_jql_transform", SCRIPT_DIR / "csv_jql_transform.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

to_jql_filename = mod.to_jql_filename
build_filter_url = mod.build_filter_url
transform_csv = mod.transform_csv
main = mod.main
JIRA_BASE_URL = mod.JIRA_BASE_URL


# ---------------------------------------------------------------------------
# to_jql_filename
# ---------------------------------------------------------------------------

class TestToJqlFilename:
    def test_basic(self):
        assert to_jql_filename("CPV IB Jira: Pollara - IB Issues") == "cpv_ib_jira_pollara_ib_issues.jql"

    def test_plus_and_pipe(self):
        assert to_jql_filename("QFAB Block 15+16+17 | CFAB Block 8") == "qfab_block_15_16_17_cfab_block_8.jql"

    def test_leading_trailing_special(self):
        assert to_jql_filename("  --Hello World-- ") == "hello_world.jql"

    def test_underscores_preserved(self):
        assert to_jql_filename("already_snake_case") == "already_snake_case.jql"

    def test_single_word(self):
        assert to_jql_filename("LVV") == "lvv.jql"

    def test_empty_string(self):
        assert to_jql_filename("") == ".jql"


# ---------------------------------------------------------------------------
# build_filter_url
# ---------------------------------------------------------------------------

class TestBuildFilterUrl:
    def test_numeric_id(self):
        assert build_filter_url("383106") == f"{JIRA_BASE_URL}?filter=383106&mode=advanced"

    def test_id_with_whitespace(self):
        assert build_filter_url("  383106  ") == f"{JIRA_BASE_URL}?filter=383106&mode=advanced"

    def test_empty_string(self):
        assert build_filter_url("") == ""

    def test_whitespace_only(self):
        assert build_filter_url("   ") == ""


# ---------------------------------------------------------------------------
# Helper to write a CSV for testing
# ---------------------------------------------------------------------------

def _write_csv(path, header, rows, encoding="utf-8", bom=False):
    """Write a CSV file. If bom=True, prepend a UTF-8 BOM."""
    with open(path, "w", newline="", encoding=encoding) as f:
        if bom:
            f.write("\ufeff")
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# transform_csv
# ---------------------------------------------------------------------------

class TestTransformCsv:
    def test_basic_transform(self, tmp_path):
        """Inserts Full Filter URL and JQL Filename columns."""
        src = tmp_path / "in.csv"
        dst = tmp_path / "out" / "out.csv"
        _write_csv(src, ["Build", "Group", "Category", "Filter", "cc"],
                   [["b1", "g1", "Some Category", "12345", "user@x"]])

        transform_csv(src, dst)

        with open(dst, newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            row = next(reader)

        assert header == ["Build", "Group", "Category", "Filter", "Full Filter URL", "JQL Filename", "cc"]
        assert row[4] == f"{JIRA_BASE_URL}?filter=12345&mode=advanced"
        assert row[5] == "some_category.jql"
        assert row[6] == "user@x"

    def test_bom_handling(self, tmp_path):
        """Handles UTF-8 BOM in source file."""
        src = tmp_path / "bom.csv"
        dst = tmp_path / "bom_out.csv"
        _write_csv(src, ["Build", "Category", "Filter"], [["b1", "Test BOM", "99"]], bom=True)

        transform_csv(src, dst)

        with open(dst, newline="") as f:
            header = next(csv.reader(f))
        assert header[0] == "Build"  # no BOM leakage

    def test_skip_already_transformed(self, tmp_path, capsys):
        """Skips files that already have a Full Filter URL column."""
        src = tmp_path / "done.csv"
        dst = tmp_path / "done_out.csv"
        _write_csv(src, ["Build", "Category", "Filter", "Full Filter URL"], [])

        transform_csv(src, dst)

        assert not dst.exists()
        assert "SKIP (already transformed)" in capsys.readouterr().out

    def test_skip_missing_filter(self, tmp_path, capsys):
        """Skips files without a Filter column."""
        src = tmp_path / "nofilt.csv"
        dst = tmp_path / "nofilt_out.csv"
        _write_csv(src, ["Build", "Category", "Other"], [])

        transform_csv(src, dst)

        assert not dst.exists()
        assert "SKIP (missing Filter or Category column)" in capsys.readouterr().out

    def test_skip_missing_category(self, tmp_path, capsys):
        """Skips files without a Category column."""
        src = tmp_path / "nocat.csv"
        dst = tmp_path / "nocat_out.csv"
        _write_csv(src, ["Build", "Filter", "Other"], [])

        transform_csv(src, dst)

        assert not dst.exists()
        assert "SKIP (missing Filter or Category column)" in capsys.readouterr().out

    def test_short_rows_padded(self, tmp_path):
        """Rows shorter than the header are padded with empty strings."""
        src = tmp_path / "short.csv"
        dst = tmp_path / "short_out.csv"
        # Header has 4 columns, row has 3 (missing cc)
        _write_csv(src, ["Build", "Category", "Filter", "cc"],
                   [["b1", "Cat A", "111"]])

        transform_csv(src, dst)

        with open(dst, newline="") as f:
            reader = csv.reader(f)
            next(reader)  # header
            row = next(reader)
        # cc should be padded to ""
        assert row[-1] == ""

    def test_whitespace_trimmed(self, tmp_path):
        """Leading/trailing whitespace in cells is stripped."""
        src = tmp_path / "ws.csv"
        dst = tmp_path / "ws_out.csv"
        _write_csv(src, ["Build", "Category", "Filter"],
                   [["  b1 ", " My Category ", " 555 "]])

        transform_csv(src, dst)

        with open(dst, newline="") as f:
            reader = csv.reader(f)
            next(reader)
            row = next(reader)
        assert row[0] == "b1"
        assert row[1] == "My Category"
        assert row[2] == "555"

    def test_jql_files_written(self, tmp_path):
        """When jql_dir is provided, .jql files are created."""
        src = tmp_path / "in.csv"
        dst = tmp_path / "out.csv"
        jql_dir = tmp_path / "jql"
        _write_csv(src, ["Build", "Category", "Filter"],
                   [["b1", "CX7 RHS Tickets", "383121"],
                    ["b2", "ILOM Issues", "383116"]])

        transform_csv(src, dst, jql_dir=jql_dir)

        assert (jql_dir / "cx7_rhs_tickets.jql").read_text() == "filter = 383121\n"
        assert (jql_dir / "ilom_issues.jql").read_text() == "filter = 383116\n"

    def test_jql_skips_empty_filter(self, tmp_path, capsys):
        """Rows with empty filter ID don't produce .jql files."""
        src = tmp_path / "in.csv"
        dst = tmp_path / "out.csv"
        jql_dir = tmp_path / "jql"
        _write_csv(src, ["Build", "Category", "Filter"],
                   [["b1", "Has Filter", "100"],
                    ["b2", "No Filter", ""]])

        transform_csv(src, dst, jql_dir=jql_dir)

        assert (jql_dir / "has_filter.jql").exists()
        assert not (jql_dir / "no_filter.jql").exists()
        assert "wrote 1 .jql file(s)" in capsys.readouterr().out

    def test_jql_dir_created(self, tmp_path):
        """jql_dir is created if it doesn't exist."""
        src = tmp_path / "in.csv"
        dst = tmp_path / "out.csv"
        jql_dir = tmp_path / "nested" / "jql"
        _write_csv(src, ["Build", "Category", "Filter"],
                   [["b1", "Test", "1"]])

        transform_csv(src, dst, jql_dir=jql_dir)

        assert jql_dir.is_dir()

    def test_output_dir_created(self, tmp_path):
        """Output parent directories are created if they don't exist."""
        src = tmp_path / "in.csv"
        dst = tmp_path / "nested" / "deep" / "out.csv"
        _write_csv(src, ["Build", "Category", "Filter"],
                   [["b1", "Test", "1"]])

        transform_csv(src, dst)

        assert dst.exists()


# ---------------------------------------------------------------------------
# CLI (main) — in-process for coverage tracking
# ---------------------------------------------------------------------------


class TestMainCli:
    def test_single_file(self, tmp_path, capsys):
        src = tmp_path / "in.csv"
        out_dir = tmp_path / "out"
        _write_csv(src, ["Build", "Category", "Filter"],
                   [["b1", "Test", "1"]])

        with patch("sys.argv", ["prog", "-i", str(src), "-o", str(out_dir)]):
            main()

        assert (out_dir / "in.csv").exists()
        assert "Transforming single file" in capsys.readouterr().out

    def test_single_file_not_found(self, tmp_path):
        with patch("sys.argv", ["prog", "-i", str(tmp_path / "nope.csv"), "-o", str(tmp_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_directory_mode(self, tmp_path, capsys):
        in_dir = tmp_path / "csvs"
        in_dir.mkdir()
        out_dir = tmp_path / "out"
        _write_csv(in_dir / "a.csv", ["Build", "Category", "Filter"],
                   [["b1", "Cat A", "10"]])
        _write_csv(in_dir / "b.csv", ["Build", "Category", "Filter"],
                   [["b2", "Cat B", "20"]])

        with patch("sys.argv", ["prog", "-d", str(in_dir), "-o", str(out_dir)]):
            main()

        assert (out_dir / "a.csv").exists()
        assert (out_dir / "b.csv").exists()
        assert "Transforming 2 file(s)" in capsys.readouterr().out

    def test_directory_not_found(self, tmp_path):
        with patch("sys.argv", ["prog", "-d", str(tmp_path / "nope"), "-o", str(tmp_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_directory_no_csvs(self, tmp_path, capsys):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with patch("sys.argv", ["prog", "-d", str(empty_dir), "-o", str(tmp_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
        assert "No CSV files found" in capsys.readouterr().out

    def test_write_jql_flag(self, tmp_path):
        src = tmp_path / "in.csv"
        out_dir = tmp_path / "out"
        jql_dir = tmp_path / "jql"
        _write_csv(src, ["Build", "Category", "Filter"],
                   [["b1", "My Query", "42"]])

        with patch("sys.argv", ["prog", "-i", str(src), "-o", str(out_dir),
                                 "--write-jql", "--jql-dir", str(jql_dir)]):
            main()

        assert (jql_dir / "my_query.jql").read_text() == "filter = 42\n"

    def test_jql_dir_implies_write(self, tmp_path):
        """--jql-dir alone (without --write-jql) still writes .jql files."""
        src = tmp_path / "in.csv"
        out_dir = tmp_path / "out"
        jql_dir = tmp_path / "jql"
        _write_csv(src, ["Build", "Category", "Filter"],
                   [["b1", "Implied", "77"]])

        with patch("sys.argv", ["prog", "-i", str(src), "-o", str(out_dir),
                                 "--jql-dir", str(jql_dir)]):
            main()

        assert (jql_dir / "implied.jql").exists()

    def test_write_jql_uses_default_dir(self, tmp_path, capsys):
        """--write-jql without --jql-dir uses the default scripts/jql/ dir."""
        src = tmp_path / "in.csv"
        out_dir = tmp_path / "out"
        default_jql = tmp_path / "default_jql"
        _write_csv(src, ["Build", "Category", "Filter"],
                   [["b1", "Default Dir Test", "88"]])

        with patch("sys.argv", ["prog", "-i", str(src), "-o", str(out_dir), "--write-jql"]), \
             patch.object(mod, "DEFAULT_JQL_DIR", str(default_jql)):
            main()

        out = capsys.readouterr().out
        assert "JQL: wrote 1 .jql file(s)" in out
        assert (default_jql / "default_dir_test.jql").exists()

    def test_done_printed(self, tmp_path, capsys):
        src = tmp_path / "in.csv"
        _write_csv(src, ["Build", "Category", "Filter"],
                   [["b1", "T", "1"]])

        with patch("sys.argv", ["prog", "-i", str(src), "-o", str(tmp_path / "out")]):
            main()

        assert "Done." in capsys.readouterr().out
