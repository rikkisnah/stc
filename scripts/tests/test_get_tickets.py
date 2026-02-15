"""Tests for get_tickets.py"""

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Import hyphenated module
get_tickets = importlib.import_module("get_tickets")
archive_existing = get_tickets.archive_existing
build_date_filter = get_tickets.build_date_filter
fetch_search = get_tickets.fetch_search
fetch_single_ticket = get_tickets.fetch_single_ticket
load_jql_from_file = get_tickets.load_jql_from_file
parse_args = get_tickets.parse_args
parse_ticket_key = get_tickets.parse_ticket_key
load_jira_token = get_tickets.load_jira_token
load_tickets_file = get_tickets.load_tickets_file
fetch_tickets_from_file = get_tickets.fetch_tickets_from_file



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

    def test_prefers_last_date_filter_range_over_relative(self):
        args = parse_args(["-a", "-1d", "2026-01-01", "2026-01-02"])
        assert args.relative_days is None
        assert args.start_date == "2026-01-01"
        assert args.end_date == "2026-01-02"

    def test_prefers_last_date_filter_relative_over_range(self):
        args = parse_args(["-a", "2026-01-01", "2026-01-02", "-1d"])
        assert args.relative_days == 1
        assert args.start_date is None
        assert args.end_date is None

    def test_extra_positional_ignored_when_date_filter_present(self):
        # Extra tokens should not abort the run; we pick the last valid filter.
        args = parse_args(["-a", "2025-01-01", "2025-01-31", "extra"])
        assert args.start_date == "2025-01-01"
        assert args.end_date == "2025-01-31"

    def test_invalid_date_range(self):
        with pytest.raises(SystemExit):
            parse_args(["-a", "2025-01-01", "bad"])

    def test_jql_file_flag_records_path(self, tmp_path):
        jql_file = tmp_path / "custom.jql"
        jql_file.write_text("project = \"DC Ops\"")
        args = parse_args(["-a", "--jql-file", str(jql_file)])
        assert getattr(args, "jql_file") == str(jql_file)

    def test_jql_file_flag_requires_fetch_all(self, tmp_path):
        jql_file = tmp_path / "custom.jql"
        jql_file.write_text("project = \"DC Ops\"")
        with pytest.raises(SystemExit):
            parse_args(["--jql-file", str(jql_file)])

    def test_include_resolved_only_flag(self):
        args = parse_args(["-a", "--include-resolved-only"])
        assert args.include_resolved_only is True

    def test_include_resolved_only_conflicts_with_include_unresolved(self):
        with pytest.raises(SystemExit):
            parse_args(["-a", "--include-resolved-only", "--include-unresolved"])

    def test_include_resolved_only_conflicts_with_unresolved_only(self):
        with pytest.raises(SystemExit):
            parse_args(["-a", "--include-resolved-only", "--unresolved-only"])

    def test_number_of_tickets_sets_value_and_default_output_path(self):
        args = parse_args(["-a", "--number-of-tickets", "5"])
        assert args.number_of_tickets == 5
        expected_default = get_tickets.OUTPUT_DIR / "limited-tickets.json"
        assert args.output_file == str(expected_default)

    @pytest.mark.parametrize("invalid", ["0", "-1", "-10"])
    def test_number_of_tickets_requires_positive_integer(self, invalid):
        with pytest.raises(SystemExit):
            parse_args(["-a", "--number-of-tickets", invalid])

    def test_number_of_tickets_requires_fetch_all(self):
        with pytest.raises(SystemExit):
            parse_args(["--number-of-tickets", "5"])

    def test_output_file_requires_number_of_tickets(self, tmp_path):
        target = tmp_path / "subset.json"
        with pytest.raises(SystemExit):
            parse_args(["-a", "--output-file", str(target)])


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


# --- load_jira_token ---


class TestLoadJiraToken:
    def test_reads_from_env_json(self, tmp_path, monkeypatch, capsys):
        env_path = tmp_path / "env.json"
        env_path.write_text(json.dumps({"jira_token": "TOKEN_FROM_FILE"}))
        monkeypatch.setattr(get_tickets, "CONFIG_ENV_PATH", env_path)

        token = load_jira_token()
        assert token == "TOKEN_FROM_FILE"
        assert f"Using Jira token from {env_path}." in capsys.readouterr().out

    def test_placeholder_falls_back_to_embedded(self, tmp_path, monkeypatch, capsys):
        env_path = tmp_path / "env.json"
        env_path.write_text(json.dumps({"jira_token": "PLACEHOLDER"}))
        monkeypatch.setattr(get_tickets, "CONFIG_ENV_PATH", env_path)

        token = load_jira_token()
        assert token == get_tickets.DEFAULT_JIRA_TOKEN
        out = capsys.readouterr().out
        assert "missing/placeholder" in out
        assert "Using embedded Jira token." in out

    def test_missing_file_falls_back_to_embedded(self, tmp_path, monkeypatch, capsys):
        env_path = tmp_path / "env.json"
        monkeypatch.setattr(get_tickets, "CONFIG_ENV_PATH", env_path)

        token = load_jira_token()
        assert token == get_tickets.DEFAULT_JIRA_TOKEN
        out = capsys.readouterr().out
        assert "not found" in out
        assert "Using embedded Jira token." in out


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

    def test_custom_jql_file_content_used(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        custom_jql = "project = \"DC Ops\" AND status = \"Open\""
        responses = iter([
            {"issues": [], "total": 0},
        ])
        mock_get = MagicMock(side_effect=lambda *a, **kw: MagicMock(json=MagicMock(return_value=next(responses))))
        monkeypatch.setattr(get_tickets.requests, "get", mock_get)

        fetch_search(jql=custom_jql)

        params = mock_get.call_args[1]["params"]
        assert params["jql"].startswith(custom_jql)

    def test_custom_jql_empty_falls_back(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        responses = iter([
            {"issues": [], "total": 0},
        ])
        mock_get = MagicMock(side_effect=lambda *a, **kw: MagicMock(json=MagicMock(return_value=next(responses))))
        monkeypatch.setattr(get_tickets.requests, "get", mock_get)

        fetch_search(jql="")

        params = mock_get.call_args[1]["params"]
        assert params["jql"].startswith(get_tickets.BASE_JQL)

    def test_number_of_tickets_sets_max_results_and_stops(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        responses = iter([
            {"issues": [{"key": "DO-1"}, {"key": "DO-2"}, {"key": "DO-3"}], "total": 50},
            {"issues": [], "total": 50},
        ])
        captured_max = []

        def fake_get(*args, **kwargs):
            captured_max.append(kwargs["params"]["maxResults"])
            return MagicMock(json=MagicMock(return_value=next(responses)))

        monkeypatch.setattr(get_tickets.requests, "get", fake_get)

        fetch_search(number_of_tickets=2, output_file=str(tmp_path / "subset.json"))

        assert captured_max == [2]

    def test_number_of_tickets_writes_output_file_only(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        responses = iter([
            {"issues": [{"key": "DO-1"}], "total": 50},
            {"issues": [{"key": "DO-2"}], "total": 50},
        ])

        def fake_get(*args, **kwargs):
            return MagicMock(json=MagicMock(return_value=next(responses, {"issues": [], "total": 50})))

        monkeypatch.setattr(get_tickets.requests, "get", fake_get)

        limited_path = tmp_path / "limited.json"
        fetch_search(number_of_tickets=2, output_file=str(limited_path))

        assert limited_path.exists()
        limited_data = json.loads(limited_path.read_text())
        assert [ticket["key"] for ticket in limited_data["issues"]] == ["DO-1", "DO-2"]
        assert limited_data["total"] == 50
        assert limited_data["fetched"] == 2
        assert limited_data["limited"] is True
        assert not list(tmp_path.glob("page_*.json"))

    def test_number_of_tickets_payload_preserves_true_total(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        responses = iter([
            {"issues": [{"key": "DO-1"}, {"key": "DO-1b"}], "total": 50},
            {"issues": [{"key": "DO-2"}, {"key": "DO-2b"}], "total": 50},
        ])

        def fake_get(*args, **kwargs):
            return MagicMock(json=MagicMock(return_value=next(responses, {"issues": [], "total": 50})))

        monkeypatch.setattr(get_tickets.requests, "get", fake_get)

        limited_path = tmp_path / "limited.json"
        fetch_search(number_of_tickets=3, output_file=str(limited_path))

        limited_data = json.loads(limited_path.read_text())
        assert limited_data["total"] == 50
        assert limited_data["fetched"] == 3
        assert len(limited_data["issues"]) == 3
        assert limited_data["limited"] is True


class TestMainLimitedFetch:
    def test_threads_number_of_tickets_into_fetch_search(self, tmp_path, monkeypatch):
        captured = {}

        def fake_fetch_search(*args, **kwargs):
            captured["called"] = True
            captured["kwargs"] = kwargs

        monkeypatch.setattr(get_tickets, "fetch_search", fake_fetch_search)
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        get_tickets.main(["-a", "--number-of-tickets", "2"])

        assert captured.get("called") is True
        assert captured["kwargs"]["number_of_tickets"] == 2
        expected_default = tmp_path / "limited-tickets.json"
        assert captured["kwargs"]["output_file"] == str(expected_default)

    def test_threads_custom_output_file_to_fetch_search(self, tmp_path, monkeypatch):
        captured = {}

        def fake_fetch_search(*args, **kwargs):
            captured["kwargs"] = kwargs

        monkeypatch.setattr(get_tickets, "fetch_search", fake_fetch_search)
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        custom_path = tmp_path / "subset.json"
        get_tickets.main([
            "-a",
            "--number-of-tickets",
            "3",
            "--output-file",
            str(custom_path),
        ])

        assert captured["kwargs"]["number_of_tickets"] == 3
        assert captured["kwargs"]["output_file"] == str(custom_path)


# --- load_jql_from_file ---

class TestLoadJqlFromFile:
    def test_returns_stripped_content(self, tmp_path):
        f = tmp_path / "test.jql"
        f.write_text("  project = DC  \n")
        assert load_jql_from_file(str(f)) == "project = DC"

    def test_empty_file_returns_none(self, tmp_path, capsys):
        f = tmp_path / "empty.jql"
        f.write_text("   \n")
        assert load_jql_from_file(str(f)) is None
        assert "empty" in capsys.readouterr().out

    def test_missing_file_returns_none(self, capsys):
        assert load_jql_from_file("/nonexistent/path.jql") is None
        assert "failed reading" in capsys.readouterr().out


# --- _extract_positional_tokens ---

class TestExtractPositionalTokens:
    def test_double_dash_separator(self):
        result = get_tickets._extract_positional_tokens(["-a", "--", "-2d", "--yes"])
        assert result == ["-2d", "--yes"]

    def test_option_equals_syntax_recognized(self):
        result = get_tickets._extract_positional_tokens(
            ["--jql-file=/path/f.jql", "2025-01-01"]
        )
        assert result == ["2025-01-01"]

    def test_option_equals_syntax_unrecognized_treated_as_positional(self):
        result = get_tickets._extract_positional_tokens(["--unknown=value"])
        assert result == ["--unknown=value"]


# --- additional parse_args edge cases ---

class TestParseArgsEdgeCases:
    def test_uses_sys_argv_when_argv_is_none(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["get_tickets.py", "-a"])
        args = parse_args()
        assert args.fetch_all is True

    def test_date_filter_without_action_shows_help(self):
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["-2d"])
        assert exc_info.value.code == 0


# --- additional load_jira_token edge cases ---

class TestLoadJiraTokenEdgeCases:
    def test_invalid_json_falls_back_to_embedded(self, tmp_path, monkeypatch, capsys):
        env_path = tmp_path / "env.json"
        env_path.write_text("{invalid json")
        monkeypatch.setattr(get_tickets, "CONFIG_ENV_PATH", env_path)

        token = load_jira_token()
        assert token == get_tickets.DEFAULT_JIRA_TOKEN
        out = capsys.readouterr().out
        assert "failed reading" in out
        assert "Using embedded Jira token." in out


# --- additional fetch_search edge cases ---

class TestFetchSearchEdgeCases:
    def test_unresolved_only_filter(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        empty = {"issues": [], "total": 0}
        mock_resp = MagicMock()
        mock_resp.json.return_value = empty
        mock_get = MagicMock(return_value=mock_resp)
        monkeypatch.setattr(get_tickets.requests, "get", mock_get)

        fetch_search(unresolved_only=True)

        call_params = mock_get.call_args[1]["params"]
        assert "resolution = Unresolved" in call_params["jql"]

    def test_include_resolved_only_filter(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        empty = {"issues": [], "total": 0}
        mock_resp = MagicMock()
        mock_resp.json.return_value = empty
        mock_get = MagicMock(return_value=mock_resp)
        monkeypatch.setattr(get_tickets.requests, "get", mock_get)

        fetch_search(include_resolved_only=True)

        call_params = mock_get.call_args[1]["params"]
        assert "resolution = Resolved" in call_params["jql"]

    def test_limited_mode_requires_output_file(self):
        with pytest.raises(ValueError, match="output_file is required"):
            fetch_search(number_of_tickets=5, output_file=None)


# --- main() edge cases ---

class TestMainEdgeCases:
    def test_invalid_ticket_key_exits(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            get_tickets.main(["-t", "not-valid-key"])
        assert exc_info.value.code == 1
        assert "Invalid ticket key" in capsys.readouterr().err

    def test_valid_ticket_calls_fetch(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"key": "DO-123", "fields": {"summary": "Test"}}
        monkeypatch.setattr(get_tickets.requests, "get", lambda *a, **kw: mock_resp)

        get_tickets.main(["-t", "DO-123"])

        assert (tmp_path / "DO-123.json").exists()


# --- load_tickets_file ---

class TestLoadTicketsFile:
    def test_simple_keys(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("DO-123\nHPC-456\n")
        result = load_tickets_file(str(f))
        assert result == ["DO-123", "HPC-456"]

    def test_skips_blank_lines(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("DO-123\n\n  \nHPC-456\n")
        result = load_tickets_file(str(f))
        assert result == ["DO-123", "HPC-456"]

    def test_skips_comments(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("# This is a comment\nDO-123\n# Another comment\nHPC-456\n")
        result = load_tickets_file(str(f))
        assert result == ["DO-123", "HPC-456"]

    def test_strips_whitespace(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("  DO-123  \n  HPC-456\t\n")
        result = load_tickets_file(str(f))
        assert result == ["DO-123", "HPC-456"]

    def test_deduplicates_preserving_order(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("DO-123\nHPC-456\nDO-123\nHPC-789\nHPC-456\n")
        result = load_tickets_file(str(f))
        assert result == ["DO-123", "HPC-456", "HPC-789"]

    def test_accepts_browse_urls(self, tmp_path):
        f = tmp_path / "tickets.txt"
        url = "https://jira-sd.mc1.oracleiaas.com/browse/DO-123"
        f.write_text(f"{url}\nHPC-456\n")
        result = load_tickets_file(str(f))
        assert result == ["DO-123", "HPC-456"]

    def test_invalid_key_exits(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("DO-123\nnot-a-ticket\nHPC-456\n")
        with pytest.raises(SystemExit) as exc_info:
            load_tickets_file(str(f))
        assert exc_info.value.code == 1

    def test_empty_file_exits(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("# only comments\n\n  \n")
        with pytest.raises(SystemExit) as exc_info:
            load_tickets_file(str(f))
        assert exc_info.value.code == 1

    def test_missing_file_exits(self):
        with pytest.raises(SystemExit) as exc_info:
            load_tickets_file("/nonexistent/tickets.txt")
        assert exc_info.value.code == 1

    def test_all_invalid_exits(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("bad-key\nworse-key\n")
        with pytest.raises(SystemExit) as exc_info:
            load_tickets_file(str(f))
        assert exc_info.value.code == 1


# --- fetch_tickets_from_file ---

class TestFetchTicketsFromFile:
    def test_fetches_all_keys(self, tmp_path, monkeypatch):
        tickets_file = tmp_path / "tickets.txt"
        tickets_file.write_text("DO-123\nDO-456\n")
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        fetched = []
        monkeypatch.setattr(get_tickets, "fetch_single_ticket",
                            lambda k: fetched.append(k))

        fetch_tickets_from_file(str(tickets_file), force=True)
        assert fetched == ["DO-123", "DO-456"]

    def test_archives_existing_with_force(self, tmp_path, monkeypatch):
        tickets_file = tmp_path / "tickets.txt"
        tickets_file.write_text("DO-123\n")

        out_dir = tmp_path / "output"
        out_dir.mkdir()
        (out_dir / "old.json").write_text("{}")
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", out_dir)
        monkeypatch.setattr(get_tickets, "fetch_single_ticket", lambda k: None)

        fetch_tickets_from_file(str(tickets_file), force=True)
        assert not (out_dir / "old.json").exists()

    def test_deduplicates_keys(self, tmp_path, monkeypatch):
        tickets_file = tmp_path / "tickets.txt"
        tickets_file.write_text("DO-123\nDO-456\nDO-123\n")
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        fetched = []
        monkeypatch.setattr(get_tickets, "fetch_single_ticket",
                            lambda k: fetched.append(k))

        fetch_tickets_from_file(str(tickets_file), force=True)
        assert fetched == ["DO-123", "DO-456"]

    def test_prints_summary(self, tmp_path, monkeypatch, capsys):
        tickets_file = tmp_path / "tickets.txt"
        tickets_file.write_text("DO-123\nDO-456\n")
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)
        monkeypatch.setattr(get_tickets, "fetch_single_ticket", lambda k: None)

        fetch_tickets_from_file(str(tickets_file), force=True)
        out = capsys.readouterr().out
        assert "2 unique ticket(s)" in out
        assert "Fetched 2 ticket(s) from file" in out


# --- parse_args --tickets-file ---

class TestParseArgsTicketsFile:
    def test_tickets_file_short_flag(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("DO-123\n")
        args = parse_args(["-f", str(f)])
        assert args.tickets_file == str(f)

    def test_tickets_file_long_flag(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("DO-123\n")
        args = parse_args(["--tickets-file", str(f)])
        assert args.tickets_file == str(f)

    def test_tickets_file_with_yes(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("DO-123\n")
        args = parse_args(["-f", str(f), "-y"])
        assert args.tickets_file == str(f)
        assert args.yes is True

    def test_mutually_exclusive_with_ticket(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("DO-123\n")
        with pytest.raises(SystemExit):
            parse_args(["-f", str(f), "-t", "DO-456"])

    def test_mutually_exclusive_with_all(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("DO-123\n")
        with pytest.raises(SystemExit):
            parse_args(["-f", str(f), "-a"])

    def test_not_set_by_default(self):
        args = parse_args(["-a"])
        assert args.tickets_file is None


# --- _extract_positional_tokens --tickets-file ---

class TestExtractPositionalTokensTicketsFile:
    def test_short_flag_consumed(self):
        result = get_tickets._extract_positional_tokens(
            ["-f", "/path/to/file.txt", "2025-01-01"])
        assert result == ["2025-01-01"]

    def test_long_flag_consumed(self):
        result = get_tickets._extract_positional_tokens(
            ["--tickets-file", "/path/to/file.txt", "2025-01-01"])
        assert result == ["2025-01-01"]


# --- main() --tickets-file dispatch ---

class TestMainTicketsFile:
    def test_dispatches_to_fetch_tickets_from_file(self, tmp_path, monkeypatch):
        tickets_file = tmp_path / "tickets.txt"
        tickets_file.write_text("DO-123\n")
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        captured = {}
        def fake_fetch(path, force=False):
            captured["path"] = path
            captured["force"] = force
        monkeypatch.setattr(get_tickets, "fetch_tickets_from_file", fake_fetch)

        get_tickets.main(["-f", str(tickets_file)])
        assert captured["path"] == str(tickets_file)
        assert captured["force"] is False

    def test_dispatches_with_force(self, tmp_path, monkeypatch):
        tickets_file = tmp_path / "tickets.txt"
        tickets_file.write_text("DO-123\n")
        monkeypatch.setattr(get_tickets, "OUTPUT_DIR", tmp_path)

        captured = {}
        def fake_fetch(path, force=False):
            captured["force"] = force
        monkeypatch.setattr(get_tickets, "fetch_tickets_from_file", fake_fetch)

        get_tickets.main(["-f", str(tickets_file), "-y"])
        assert captured["force"] is True
