"""Tests for get-tickets.py"""

import importlib
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Import hyphenated module
get_tickets = importlib.import_module("get-tickets")
archive_existing = get_tickets.archive_existing
build_date_filter = get_tickets.build_date_filter
fetch_search = get_tickets.fetch_search
fetch_single_ticket = get_tickets.fetch_single_ticket
parse_args = get_tickets.parse_args
parse_ticket_key = get_tickets.parse_ticket_key


# --- parse_ticket_key ---

class TestParseTicketKey:
    def test_plain_key(self):
        assert parse_ticket_key("DO-2639750") == "DO-2639750"

    def test_url(self):
        url = "https://jira-sd.mc1.oracleiaas.com/browse/DO-2639750"
        assert parse_ticket_key(url) == "DO-2639750"

    def test_invalid_returns_none(self):
        assert parse_ticket_key("not-a-ticket") is None

    def test_url_different_project(self):
        url = "https://jira-sd.mc1.oracleiaas.com/browse/HPC-12345"
        assert parse_ticket_key(url) == "HPC-12345"


# --- parse_args ---

class TestParseArgs:
    def test_no_args_shows_help(self):
        with pytest.raises(SystemExit) as exc_info:
            parse_args([])
        assert exc_info.value.code == 0

    def test_all_flag(self):
        args = parse_args(["-a"])
        assert args.fetch_all is True
        assert args.relative_days is None

    def test_all_with_relative_days(self):
        args = parse_args(["-a", "-2d"])
        assert args.fetch_all is True
        assert args.relative_days == 2

    def test_all_with_relative_days_large(self):
        args = parse_args(["-a", "-30d"])
        assert args.relative_days == 30

    def test_all_with_start_date(self):
        args = parse_args(["-a", "2025-01-01"])
        assert args.fetch_all is True
        assert args.start_date == "2025-01-01"
        assert args.end_date is None

    def test_all_with_date_range(self):
        args = parse_args(["-a", "2025-01-01", "2025-01-31"])
        assert args.start_date == "2025-01-01"
        assert args.end_date == "2025-01-31"

    def test_ticket_flag_key(self):
        args = parse_args(["-t", "DO-123"])
        assert args.ticket == "DO-123"

    def test_ticket_flag_url(self):
        url = "https://jira-sd.mc1.oracleiaas.com/browse/DO-123"
        args = parse_args(["-t", url])
        assert args.ticket == url

    def test_invalid_positional(self):
        with pytest.raises(SystemExit):
            parse_args(["-a", "not-valid"])

    def test_too_many_positional(self):
        with pytest.raises(SystemExit):
            parse_args(["-a", "2025-01-01", "2025-01-31", "extra"])

    def test_invalid_date_range(self):
        with pytest.raises(SystemExit):
            parse_args(["-a", "2025-01-01", "bad"])


# --- build_date_filter ---

class TestBuildDateFilter:
    def test_no_filter(self):
        args = parse_args(["-a"])
        assert build_date_filter(args) == ""

    def test_relative_days(self, capsys):
        args = parse_args(["-a", "-7d"])
        result = build_date_filter(args)
        assert result == ' AND created >= "-7d"'
        assert "last 7 day(s)" in capsys.readouterr().out

    def test_start_date(self, capsys):
        args = parse_args(["-a", "2025-03-01"])
        result = build_date_filter(args)
        assert result == ' AND created >= "2025-03-01"'
        assert "2025-03-01 to now" in capsys.readouterr().out

    def test_date_range(self, capsys):
        args = parse_args(["-a", "2025-01-01", "2025-06-30"])
        result = build_date_filter(args)
        assert ' AND created >= "2025-01-01"' in result
        assert ' AND created <= "2025-06-30"' in result
        assert "2025-01-01 to 2025-06-30" in capsys.readouterr().out


# --- archive_existing ---

class TestArchiveExisting:
    def test_archives_with_force(self, tmp_path):
        out_dir = tmp_path / "tickets_json"
        out_dir.mkdir()
        (out_dir / "page_0.json").write_text('{"issues": []}')
        (out_dir / "DO-123.json").write_text('{"key": "DO-123"}')

        archive_path = archive_existing(out_dir, force=True)

        assert archive_path is not None
        assert archive_path.endswith(".zip")
        assert Path(archive_path).exists()
        # JSON files should be deleted
        assert list(out_dir.glob("*.json")) == []

    def test_archives_with_user_yes(self, tmp_path, monkeypatch):
        out_dir = tmp_path / "tickets_json"
        out_dir.mkdir()
        (out_dir / "page_0.json").write_text('{"issues": []}')

        monkeypatch.setattr("builtins.input", lambda _: "y")
        archive_path = archive_existing(out_dir)

        assert archive_path is not None
        assert list(out_dir.glob("*.json")) == []

    def test_aborts_with_user_no(self, tmp_path, monkeypatch):
        out_dir = tmp_path / "tickets_json"
        out_dir.mkdir()
        (out_dir / "page_0.json").write_text('{"issues": []}')

        monkeypatch.setattr("builtins.input", lambda _: "n")
        with pytest.raises(SystemExit) as exc_info:
            archive_existing(out_dir)
        assert exc_info.value.code == 0
        # JSON files should still exist
        assert len(list(out_dir.glob("*.json"))) == 1

    def test_no_json_files(self, tmp_path):
        out_dir = tmp_path / "tickets_json"
        out_dir.mkdir()
        (out_dir / "readme.txt").write_text("not json")

        archive_path = archive_existing(out_dir)
        assert archive_path is None

    def test_dir_does_not_exist(self, tmp_path):
        out_dir = tmp_path / "nonexistent"
        archive_path = archive_existing(out_dir)
        assert archive_path is None


# --- fetch_single_ticket ---

class TestFetchSingleTicket:
    def test_success(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"key": "DO-123", "fields": {"summary": "Test"}}
        monkeypatch.setattr(get_tickets.requests, "get", lambda *a, **kw: mock_resp)

        fetch_single_ticket("DO-123")

        out_file = tmp_path / "DO-123.json"
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert data["key"] == "DO-123"

    def test_error_message(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"errorMessages": ["Issue does not exist"]}
        monkeypatch.setattr(get_tickets.requests, "get", lambda *a, **kw: mock_resp)

        with pytest.raises(SystemExit):
            fetch_single_ticket("DO-999999")

    def test_no_key_in_response(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"something": "unexpected"}
        monkeypatch.setattr(get_tickets.requests, "get", lambda *a, **kw: mock_resp)

        with pytest.raises(SystemExit):
            fetch_single_ticket("DO-123")


# --- fetch_search ---

class TestFetchSearch:
    def test_single_page(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        issues = [{"key": f"DO-{i}"} for i in range(3)]
        page1 = {"issues": issues, "total": 3}
        page2 = {"issues": [], "total": 3}
        responses = iter([page1, page2])
        mock_get = MagicMock(side_effect=lambda *a, **kw: MagicMock(json=MagicMock(return_value=next(responses))))
        monkeypatch.setattr(get_tickets.requests, "get", mock_get)

        fetch_search()

        assert (tmp_path / "page_0.json").exists()
        data = json.loads((tmp_path / "page_0.json").read_text())
        assert len(data["issues"]) == 3

    def test_parse_error_exits(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": "bad request"}
        monkeypatch.setattr(get_tickets.requests, "get", lambda *a, **kw: mock_resp)

        with pytest.raises(SystemExit):
            fetch_search()

    def test_with_date_filter(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        empty = {"issues": [], "total": 0}
        mock_resp = MagicMock()
        mock_resp.json.return_value = empty
        mock_get = MagicMock(return_value=mock_resp)
        monkeypatch.setattr(get_tickets.requests, "get", mock_get)

        fetch_search(' AND created >= "-2d"')

        call_params = mock_get.call_args[1]["params"]
        assert 'created >= "-2d"' in call_params["jql"]
