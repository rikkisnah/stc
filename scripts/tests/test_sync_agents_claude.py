# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted
"""Tests for sync_agents_claude.py with full module coverage."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "sync_agents_claude", SCRIPT_DIR / "sync_agents_claude.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


parse_args = mod.parse_args
files_match = mod.files_match
sync_files = mod.sync_files
main = mod.main
DEFAULT_SOURCE = mod.DEFAULT_SOURCE
DEFAULT_DESTINATION = mod.DEFAULT_DESTINATION


class TestParseArgs:
    def test_uses_default_paths(self):
        with patch.object(sys, "argv", ["sync_agents_claude.py"]):
            args = parse_args()

        assert args.source == DEFAULT_SOURCE
        assert args.destination == DEFAULT_DESTINATION
        assert args.check is False

    def test_supports_custom_paths_and_check(self, tmp_path):
        source = tmp_path / "a.md"
        destination = tmp_path / "b.md"
        with patch.object(
            sys,
            "argv",
            [
                "sync_agents_claude.py",
                "--source",
                str(source),
                "--destination",
                str(destination),
                "--check",
            ],
        ):
            args = parse_args()

        assert args.source == source
        assert args.destination == destination
        assert args.check is True


class TestFilesMatch:
    def test_returns_false_when_destination_missing(self, tmp_path):
        source = tmp_path / "AGENTS.md"
        destination = tmp_path / "CLAUDE.md"
        source.write_text("abc\n", encoding="utf-8")

        assert files_match(source, destination) is False

    def test_detects_match_and_mismatch(self, tmp_path):
        source = tmp_path / "AGENTS.md"
        destination = tmp_path / "CLAUDE.md"
        source.write_text("same\n", encoding="utf-8")
        destination.write_text("same\n", encoding="utf-8")
        assert files_match(source, destination) is True

        destination.write_text("different\n", encoding="utf-8")
        assert files_match(source, destination) is False


class TestSyncFiles:
    def test_writes_destination_and_creates_parent(self, tmp_path):
        source = tmp_path / "AGENTS.md"
        destination = tmp_path / "nested" / "CLAUDE.md"
        source.write_text("source-content\n", encoding="utf-8")

        changed = sync_files(source, destination)

        assert changed is True
        assert destination.read_text(encoding="utf-8") == "source-content\n"

    def test_returns_false_when_already_synced(self, tmp_path):
        source = tmp_path / "AGENTS.md"
        destination = tmp_path / "CLAUDE.md"
        source.write_text("same\n", encoding="utf-8")
        destination.write_text("same\n", encoding="utf-8")

        changed = sync_files(source, destination)

        assert changed is False


class TestMain:
    def test_exits_when_source_missing(self, tmp_path):
        source = tmp_path / "missing.md"
        destination = tmp_path / "CLAUDE.md"

        with patch.object(
            sys,
            "argv",
            [
                "sync_agents_claude.py",
                "--source",
                str(source),
                "--destination",
                str(destination),
            ],
        ):
            with pytest.raises(SystemExit, match=f"Source file not found: {source}"):
                main()

    def test_check_mode_passes_when_synced(self, tmp_path, capsys):
        source = tmp_path / "AGENTS.md"
        destination = tmp_path / "CLAUDE.md"
        source.write_text("same\n", encoding="utf-8")
        destination.write_text("same\n", encoding="utf-8")

        with patch.object(
            sys,
            "argv",
            [
                "sync_agents_claude.py",
                "--source",
                str(source),
                "--destination",
                str(destination),
                "--check",
            ],
        ):
            main()

        captured = capsys.readouterr()
        assert f"In sync: {source} == {destination}" in captured.out

    def test_check_mode_exits_when_out_of_sync(self, tmp_path):
        source = tmp_path / "AGENTS.md"
        destination = tmp_path / "CLAUDE.md"
        source.write_text("new\n", encoding="utf-8")
        destination.write_text("old\n", encoding="utf-8")

        with patch.object(
            sys,
            "argv",
            [
                "sync_agents_claude.py",
                "--source",
                str(source),
                "--destination",
                str(destination),
                "--check",
            ],
        ):
            with pytest.raises(SystemExit, match=f"Out of sync: {source} != {destination}"):
                main()

    def test_sync_mode_updates_destination(self, tmp_path, capsys):
        source = tmp_path / "AGENTS.md"
        destination = tmp_path / "CLAUDE.md"
        source.write_text("updated\n", encoding="utf-8")
        destination.write_text("stale\n", encoding="utf-8")

        with patch.object(
            sys,
            "argv",
            [
                "sync_agents_claude.py",
                "--source",
                str(source),
                "--destination",
                str(destination),
            ],
        ):
            main()

        captured = capsys.readouterr()
        assert destination.read_text(encoding="utf-8") == "updated\n"
        assert f"Updated {destination} from {source}" in captured.out

    def test_sync_mode_reports_when_already_up_to_date(self, tmp_path, capsys):
        source = tmp_path / "AGENTS.md"
        destination = tmp_path / "CLAUDE.md"
        source.write_text("same\n", encoding="utf-8")
        destination.write_text("same\n", encoding="utf-8")

        with patch.object(
            sys,
            "argv",
            [
                "sync_agents_claude.py",
                "--source",
                str(source),
                "--destination",
                str(destination),
            ],
        ):
            main()

        captured = capsys.readouterr()
        assert f"Already up to date: {destination}" in captured.out
