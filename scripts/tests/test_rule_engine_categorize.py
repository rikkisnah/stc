"""Tests for rule_engine_categorize.py"""

import csv
import importlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# Import module
rec = importlib.import_module("rule_engine_categorize")
parse_args = rec.parse_args
find_latest_tickets_dir = rec.find_latest_tickets_dir
load_rules = rec.load_rules
get_ticket_field_text = rec.get_ticket_field_text
get_ticket_project = rec.get_ticket_project
evaluate_ticket = rec.evaluate_ticket
compute_age = rec.compute_age
categorize_ticket = rec.categorize_ticket
main = rec.main
META_RULE_FAILURE = rec.META_RULE_FAILURE
OUTPUT_FIELDS = rec.OUTPUT_FIELDS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rule(rule_id="R001", pattern="foo", match_field="summary",
               failure_category="Some Failure", category="CAT",
               priority=100, confidence=0.95, project_key="DO",
               created_by="human", hit_count=0):
    """Build a rule dict mirroring what load_rules produces."""
    return {
        "RuleID": rule_id,
        "Rule Pattern": pattern,
        "Match Field": match_field,
        "Failure Category": failure_category,
        "Category": category,
        "Priority": priority,
        "Confidence": confidence,
        "Project Key": project_key,
        "Created By": created_by,
        "Hit Count": hit_count,
        "_re": re.compile(pattern, re.IGNORECASE),
    }


def _make_meta_rule(**kwargs):
    """Build a meta-rule (sets Runbook Present only)."""
    defaults = {"failure_category": META_RULE_FAILURE, "priority": 50, "confidence": 1.0}
    defaults.update(kwargs)
    return _make_rule(**defaults)


def _make_ticket(summary="test summary", description="test description",
                 labels=None, comments=None, key="DO-1234567",
                 project_key="DO", status="Open",
                 created="2026-01-01T00:00:00Z"):
    """Build a minimal normalized ticket dict."""
    return {
        "ticket": {
            "key": key,
            "summary": summary,
            "project": {"key": project_key},
        },
        "description": description,
        "labels": labels or [],
        "comments": comments or [],
        "status": {"current": status, "created": created},
    }


def _write_rule_csv(path, rules_data):
    """Write a rule-engine CSV from a list of row dicts."""
    fieldnames = [
        "Project Key", "RuleID", "Rule Pattern", "Match Field",
        "Failure Category", "Category", "Priority", "Confidence",
        "Created By", "Hit Count",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rules_data:
            writer.writerow(row)


def _write_ticket_json(directory, ticket_id, ticket_data):
    """Write a normalized ticket JSON file."""
    path = directory / f"{ticket_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ticket_data, f)


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------

class TestParseArgs:
    def test_defaults(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["rule_engine_categorize.py"])
        args = parse_args()
        assert args.tickets_dir is None
        assert args.rule_engine == rec.DEFAULT_RULE_ENGINE
        assert args.output_dir == rec.DEFAULT_OUTPUT_DIR
        assert args.project is None
        assert args.resume is False

    def test_custom_options(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sys.argv", [
            "rule_engine_categorize.py",
            "--tickets-dir", str(tmp_path),
            "--rule-engine", str(tmp_path / "rules.csv"),
            "--output-dir", str(tmp_path / "out"),
            "--project", "HPC",
            "--resume",
        ])
        args = parse_args()
        assert args.tickets_dir == tmp_path
        assert args.rule_engine == tmp_path / "rules.csv"
        assert args.output_dir == tmp_path / "out"
        assert args.project == "HPC"
        assert args.resume is True

    def test_project_do(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["rule_engine_categorize.py", "--project", "DO"])
        args = parse_args()
        assert args.project == "DO"

    def test_invalid_project(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["rule_engine_categorize.py", "--project", "INVALID"])
        with pytest.raises(SystemExit):
            parse_args()


# ---------------------------------------------------------------------------
# find_latest_tickets_dir
# ---------------------------------------------------------------------------

class TestFindLatestTicketsDir:
    def test_no_base_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(rec, "REPO_ROOT", tmp_path)
        with pytest.raises(SystemExit):
            find_latest_tickets_dir()

    def test_empty_base_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(rec, "REPO_ROOT", tmp_path)
        (tmp_path / "scripts" / "normalized-tickets").mkdir(parents=True)
        with pytest.raises(SystemExit):
            find_latest_tickets_dir()

    def test_picks_latest(self, tmp_path, monkeypatch):
        monkeypatch.setattr(rec, "REPO_ROOT", tmp_path)
        base = tmp_path / "scripts" / "normalized-tickets"
        (base / "2026-01-01").mkdir(parents=True)
        (base / "2026-02-15").mkdir(parents=True)
        (base / "2026-01-15").mkdir(parents=True)
        result = find_latest_tickets_dir()
        assert result == base / "2026-02-15"


# ---------------------------------------------------------------------------
# load_rules
# ---------------------------------------------------------------------------

class TestLoadRules:
    def test_loads_and_sorts(self, tmp_path):
        csv_path = tmp_path / "rules.csv"
        _write_rule_csv(csv_path, [
            {"Project Key": "DO", "RuleID": "R001", "Rule Pattern": "foo",
             "Match Field": "summary", "Failure Category": "Fail A",
             "Category": "CAT", "Priority": "50", "Confidence": "0.9",
             "Created By": "human", "Hit Count": "1"},
            {"Project Key": "DO", "RuleID": "R002", "Rule Pattern": "bar",
             "Match Field": "summary", "Failure Category": "Fail B",
             "Category": "CAT", "Priority": "100", "Confidence": "0.8",
             "Created By": "llm", "Hit Count": "0"},
        ])
        rules = load_rules(csv_path)
        assert len(rules) == 2
        # Sorted by priority desc: R002 (100) before R001 (50)
        assert rules[0]["RuleID"] == "R002"
        assert rules[1]["RuleID"] == "R001"
        # Numeric conversions
        assert rules[0]["Priority"] == 100
        assert rules[0]["Confidence"] == 0.8
        assert rules[0]["Hit Count"] == 0
        assert rules[0]["_re"] is not None

    def test_project_filter(self, tmp_path):
        csv_path = tmp_path / "rules.csv"
        _write_rule_csv(csv_path, [
            {"Project Key": "DO", "RuleID": "R001", "Rule Pattern": "foo",
             "Match Field": "summary", "Failure Category": "Fail",
             "Category": "CAT", "Priority": "100", "Confidence": "0.9",
             "Created By": "human", "Hit Count": "0"},
            {"Project Key": "HPC", "RuleID": "R002", "Rule Pattern": "bar",
             "Match Field": "summary", "Failure Category": "Fail",
             "Category": "CAT", "Priority": "90", "Confidence": "0.9",
             "Created By": "human", "Hit Count": "0"},
        ])
        rules = load_rules(csv_path, project="DO")
        assert len(rules) == 1
        assert rules[0]["RuleID"] == "R001"

    def test_bad_regex(self, tmp_path, capsys):
        csv_path = tmp_path / "rules.csv"
        _write_rule_csv(csv_path, [
            {"Project Key": "DO", "RuleID": "R999", "Rule Pattern": "[invalid",
             "Match Field": "summary", "Failure Category": "Fail",
             "Category": "CAT", "Priority": "100", "Confidence": "0.9",
             "Created By": "human", "Hit Count": "0"},
        ])
        rules = load_rules(csv_path)
        assert len(rules) == 1
        assert rules[0]["_re"] is None
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "R999" in captured.err


# ---------------------------------------------------------------------------
# get_ticket_field_text
# ---------------------------------------------------------------------------

class TestGetTicketFieldText:
    def test_summary(self):
        ticket = _make_ticket(summary="My Summary")
        assert "My Summary" in get_ticket_field_text(ticket, "summary")

    def test_description(self):
        ticket = _make_ticket(description="My Description")
        assert "My Description" in get_ticket_field_text(ticket, "description")

    def test_labels(self):
        ticket = _make_ticket(labels=["LABEL_A", "LABEL_B"])
        text = get_ticket_field_text(ticket, "labels")
        assert "LABEL_A" in text
        assert "LABEL_B" in text

    def test_comments(self):
        ticket = _make_ticket(comments=[
            {"body": "comment one"},
            {"body": "comment two"},
        ])
        text = get_ticket_field_text(ticket, "comments")
        assert "comment one" in text
        assert "comment two" in text

    def test_combined_fields(self):
        ticket = _make_ticket(summary="SUM", description="DESC")
        text = get_ticket_field_text(ticket, "summary+description")
        assert "SUM" in text
        assert "DESC" in text

    def test_unknown_field_returns_empty(self):
        ticket = _make_ticket()
        text = get_ticket_field_text(ticket, "nonexistent")
        # Unknown field produces no content, but doesn't crash
        assert text == ""


# ---------------------------------------------------------------------------
# get_ticket_project
# ---------------------------------------------------------------------------

class TestGetTicketProject:
    def test_normal(self):
        ticket = _make_ticket(project_key="HPC")
        assert get_ticket_project(ticket) == "HPC"

    def test_missing_ticket_key(self):
        assert get_ticket_project({}) == ""

    def test_missing_project_key(self):
        assert get_ticket_project({"ticket": {}}) == ""


# ---------------------------------------------------------------------------
# evaluate_ticket
# ---------------------------------------------------------------------------

class TestEvaluateTicket:
    def test_category_rule_match(self):
        ticket = _make_ticket(summary="foo bar")
        rules = [_make_rule(pattern="foo")]
        cat_rules, meta_rules = evaluate_ticket(ticket, rules)
        assert len(cat_rules) == 1
        assert len(meta_rules) == 0

    def test_meta_rule_match(self):
        ticket = _make_ticket(summary="TRS prescription found")
        rules = [_make_meta_rule(pattern="TRS prescription")]
        cat_rules, meta_rules = evaluate_ticket(ticket, rules)
        assert len(cat_rules) == 0
        assert len(meta_rules) == 1

    def test_skips_none_re(self):
        ticket = _make_ticket(summary="anything")
        rule = _make_rule(pattern="anything")
        rule["_re"] = None
        cat_rules, meta_rules = evaluate_ticket(ticket, [rule])
        assert len(cat_rules) == 0
        assert len(meta_rules) == 0

    def test_skips_wrong_project(self):
        ticket = _make_ticket(summary="foo")
        rules = [_make_rule(pattern="foo", project_key="HPC")]
        cat_rules, meta_rules = evaluate_ticket(ticket, rules, project_key="DO")
        assert len(cat_rules) == 0

    def test_no_match(self):
        ticket = _make_ticket(summary="nothing here")
        rules = [_make_rule(pattern="zzz_no_match")]
        cat_rules, meta_rules = evaluate_ticket(ticket, rules)
        assert len(cat_rules) == 0
        assert len(meta_rules) == 0

    def test_project_key_none_skips_filter(self):
        """When project_key is None, all rules are evaluated."""
        ticket = _make_ticket(summary="foo")
        rules = [_make_rule(pattern="foo", project_key="HPC")]
        cat_rules, _ = evaluate_ticket(ticket, rules, project_key=None)
        assert len(cat_rules) == 1


# ---------------------------------------------------------------------------
# compute_age
# ---------------------------------------------------------------------------

class TestComputeAge:
    def test_valid_date(self):
        yesterday = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        age = compute_age(yesterday)
        assert age == 0

    def test_z_suffix(self):
        age = compute_age("2020-01-01T00:00:00Z")
        assert isinstance(age, int)
        assert age > 0

    def test_invalid_value(self):
        assert compute_age("not-a-date") == ""

    def test_none_input(self):
        assert compute_age(None) == ""


# ---------------------------------------------------------------------------
# categorize_ticket
# ---------------------------------------------------------------------------

class TestCategorizeTicket:
    def test_rule_match(self):
        ticket = _make_ticket(summary="foo error", key="DO-111", project_key="DO",
                              status="Open", created="2026-01-15T00:00:00Z")
        rules = [_make_rule(rule_id="R001", pattern="foo", confidence=0.9)]
        row = categorize_ticket(ticket, rules)
        assert row["Ticket"] == "DO-111"
        assert row["Project Key"] == "DO"
        assert row["Category of Issue"] == "Some Failure"
        assert row["Category"] == "CAT"
        assert row["Rules Used"] == "R001"
        assert row["Categorization Source"] == "rule"
        assert row["LLM Confidence"] == 0.9
        assert row["Human Audit for Accuracy"] == "pending-review"
        assert row["Runbook Present"] == "FALSE"
        assert row["Created"] == "2026-01-15"

    def test_no_match(self):
        ticket = _make_ticket(summary="nothing")
        rules = [_make_rule(pattern="zzz")]
        row = categorize_ticket(ticket, rules)
        assert row["Category of Issue"] == "uncategorized"
        assert row["Category"] == "unknown"
        assert row["Rules Used"] == ""
        assert row["Categorization Source"] == "none"
        assert row["LLM Confidence"] == ""
        assert row["Human Audit for Accuracy"] == "needs-review"

    def test_meta_only_match(self):
        ticket = _make_ticket(summary="TRS prescription found")
        rules = [_make_meta_rule(pattern="TRS prescription")]
        row = categorize_ticket(ticket, rules)
        assert row["Runbook Present"] == "TRUE"
        assert row["Categorization Source"] == "none"
        assert row["Category of Issue"] == "uncategorized"

    def test_low_confidence_needs_review(self):
        ticket = _make_ticket(summary="foo")
        rules = [_make_rule(pattern="foo", confidence=0.3)]
        row = categorize_ticket(ticket, rules)
        assert row["Human Audit for Accuracy"] == "needs-review"

    def test_trs_extraction(self):
        ticket = _make_ticket(summary="Problem Type: TRS_DIMM_REPLACEMENT action")
        rules = [_make_rule(pattern="TRS_\\w+", category="TRS",
                            failure_category="TRS Component Replacement")]
        row = categorize_ticket(ticket, rules)
        assert row["Category"] == "TRS_DIMM_REPLACEMENT"

    def test_trs_no_match_stays_trs(self):
        ticket = _make_ticket(summary="Some TRS thing without code")
        rules = [_make_rule(pattern="TRS thing", category="TRS",
                            failure_category="TRS Component")]
        row = categorize_ticket(ticket, rules)
        assert row["Category"] == "TRS"

    def test_prescriptive_extraction(self):
        ticket = _make_ticket(
            summary="[Prescriptive Action] Serial: 2551XK106X, RESEAT CHASSIS"
        )
        rules = [_make_rule(pattern="Prescriptive Action", category="PRESCRIPTIVE",
                            failure_category="Prescriptive Action - Component")]
        row = categorize_ticket(ticket, rules)
        assert row["Category"] == "CHASSIS"

    def test_prescriptive_no_match_stays(self):
        ticket = _make_ticket(summary="Some prescriptive note")
        rules = [_make_rule(pattern="prescriptive", category="PRESCRIPTIVE",
                            failure_category="Prescriptive Action")]
        row = categorize_ticket(ticket, rules)
        assert row["Category"] == "PRESCRIPTIVE"

    def test_multiple_category_rules_uses_first(self):
        """Rules are pre-sorted by priority desc; top rule wins for category."""
        ticket = _make_ticket(summary="foo bar")
        rules = [
            _make_rule(rule_id="R002", pattern="foo", priority=100,
                       failure_category="High Priority", category="HIGH"),
            _make_rule(rule_id="R001", pattern="bar", priority=50,
                       failure_category="Low Priority", category="LOW"),
        ]
        row = categorize_ticket(ticket, rules)
        assert row["Category of Issue"] == "High Priority"
        assert row["Category"] == "HIGH"
        assert row["Rules Used"] == "R002,R001"

    def test_project_key_filter_in_categorize(self):
        ticket = _make_ticket(summary="foo", project_key="DO")
        rules = [_make_rule(pattern="foo", project_key="HPC")]
        row = categorize_ticket(ticket, rules, project_key="DO")
        assert row["Categorization Source"] == "none"

    def test_empty_created_date(self):
        ticket = _make_ticket(created="")
        ticket["status"]["created"] = ""
        rules = [_make_rule(pattern="zzz")]
        row = categorize_ticket(ticket, rules)
        assert row["Created"] == ""
        assert row["Age"] == ""


# ---------------------------------------------------------------------------
# main (integration)
# ---------------------------------------------------------------------------

class TestMain:
    def _setup_env(self, tmp_path, tickets=None, rules_data=None,
                   project_filter=None, resume=False):
        """Create tickets dir, rule engine CSV, and return argv list."""
        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()
        output_dir = tmp_path / "output"

        # Default rule
        if rules_data is None:
            rules_data = [
                {"Project Key": "DO", "RuleID": "R001",
                 "Rule Pattern": "CDFP fault", "Match Field": "summary",
                 "Failure Category": "CDFP Fault", "Category": "CDFP",
                 "Priority": "100", "Confidence": "0.95",
                 "Created By": "human", "Hit Count": "0"},
                {"Project Key": "DO", "RuleID": "R011",
                 "Rule Pattern": "TRS prescription", "Match Field": "comments",
                 "Failure Category": META_RULE_FAILURE, "Category": "HW- General",
                 "Priority": "50", "Confidence": "1",
                 "Created By": "human", "Hit Count": "0"},
            ]
        rules_csv = tmp_path / "rules.csv"
        _write_rule_csv(rules_csv, rules_data)

        # Default tickets
        if tickets is None:
            tickets = [
                ("DO-1111111", _make_ticket(
                    key="DO-1111111", summary="CDFP fault detected",
                    status="Open", created="2026-01-01T00:00:00Z")),
                ("DO-2222222", _make_ticket(
                    key="DO-2222222", summary="no match here",
                    status="Closed", created="2026-02-01T00:00:00Z")),
                ("DO-3333333", _make_ticket(
                    key="DO-3333333", summary="unrelated",
                    comments=[{"body": "TRS prescription issued"}],
                    status="Open", created="2026-01-15T00:00:00Z")),
            ]
        for tid, tdata in tickets:
            _write_ticket_json(tickets_dir, tid, tdata)

        argv = [
            "--tickets-dir", str(tickets_dir),
            "--rule-engine", str(rules_csv),
            "--output-dir", str(output_dir),
        ]
        if project_filter:
            argv.extend(["--project", project_filter])
        if resume:
            argv.append("--resume")
        return argv, output_dir

    def test_normal_run(self, tmp_path):
        argv, output_dir = self._setup_env(tmp_path)
        with patch("sys.argv", ["rule_engine_categorize.py"] + argv):
            main()
        csv_path = output_dir / "tickets-categorized.csv"
        assert csv_path.is_file()
        with open(csv_path, encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
        assert len(reader) == 3
        # Verify one rule-matched, two not
        sources = [r["Categorization Source"] for r in reader]
        assert "rule" in sources
        assert "none" in sources

    def test_project_filter(self, tmp_path):
        argv, output_dir = self._setup_env(tmp_path, project_filter="DO")
        with patch("sys.argv", ["rule_engine_categorize.py"] + argv):
            main()
        csv_path = output_dir / "tickets-categorized.csv"
        with open(csv_path, encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
        assert len(reader) == 3

    def test_tickets_dir_not_found(self, tmp_path):
        argv = [
            "--tickets-dir", str(tmp_path / "nonexistent"),
            "--rule-engine", str(tmp_path / "rules.csv"),
        ]
        # Need a valid rule engine file for the check to reach tickets dir check
        rules_csv = tmp_path / "rules.csv"
        _write_rule_csv(rules_csv, [])
        with patch("sys.argv", ["rule_engine_categorize.py"] + argv):
            with pytest.raises(SystemExit):
                main()

    def test_rule_engine_not_found(self, tmp_path):
        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()
        argv = [
            "--tickets-dir", str(tickets_dir),
            "--rule-engine", str(tmp_path / "nonexistent.csv"),
        ]
        with patch("sys.argv", ["rule_engine_categorize.py"] + argv):
            with pytest.raises(SystemExit):
                main()

    def test_no_ticket_files(self, tmp_path):
        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()
        rules_csv = tmp_path / "rules.csv"
        _write_rule_csv(rules_csv, [])
        argv = [
            "--tickets-dir", str(tickets_dir),
            "--rule-engine", str(rules_csv),
            "--output-dir", str(tmp_path / "output"),
        ]
        with patch("sys.argv", ["rule_engine_categorize.py"] + argv):
            main()
        # No output file created when no tickets
        assert not (tmp_path / "output" / "tickets-categorized.csv").is_file()

    def test_resume_skips_done(self, tmp_path, capsys):
        # First run
        argv, output_dir = self._setup_env(tmp_path)
        with patch("sys.argv", ["rule_engine_categorize.py"] + argv):
            main()
        csv_path = output_dir / "tickets-categorized.csv"
        with open(csv_path, encoding="utf-8") as f:
            first_run = list(csv.DictReader(f))
        assert len(first_run) == 3

        # Resume run — same tickets dir, same output, should skip all 3
        argv_resume = [
            "--tickets-dir", argv[1],
            "--rule-engine", argv[3],
            "--output-dir", str(output_dir),
            "--resume",
        ]
        with patch("sys.argv", ["rule_engine_categorize.py"] + argv_resume):
            main()
        captured = capsys.readouterr().out
        assert "Resuming" in captured
        assert "Skipped" in captured
        # File should still have 3 rows (appended 0 new)
        with open(csv_path, encoding="utf-8") as f:
            resumed = list(csv.DictReader(f))
        assert len(resumed) == 3

    def test_setup_env_resume_flag(self, tmp_path):
        """_setup_env with resume=True includes --resume in argv."""
        argv, output_dir = self._setup_env(tmp_path, resume=True)
        assert "--resume" in argv
        with patch("sys.argv", ["rule_engine_categorize.py"] + argv):
            main()
        csv_path = output_dir / "tickets-categorized.csv"
        assert csv_path.is_file()

    def test_default_tickets_dir(self, tmp_path, monkeypatch):
        """When --tickets-dir is not given, find_latest_tickets_dir is used."""
        monkeypatch.setattr(rec, "REPO_ROOT", tmp_path)
        base = tmp_path / "scripts" / "normalized-tickets" / "2026-02-12"
        base.mkdir(parents=True)
        _write_ticket_json(base, "DO-9999999", _make_ticket(
            key="DO-9999999", summary="test ticket"))

        rules_csv = tmp_path / "rules.csv"
        _write_rule_csv(rules_csv, [])
        output_dir = tmp_path / "output"

        argv = [
            "--rule-engine", str(rules_csv),
            "--output-dir", str(output_dir),
        ]
        with patch("sys.argv", ["rule_engine_categorize.py"] + argv):
            main()
        csv_path = output_dir / "tickets-categorized.csv"
        assert csv_path.is_file()

    def test_auto_detect_project(self, tmp_path):
        """Without --project, per-ticket project is auto-detected."""
        tickets = [
            ("DO-1111111", _make_ticket(
                key="DO-1111111", summary="CDFP fault detected",
                project_key="DO")),
            ("HPC-2222222", _make_ticket(
                key="HPC-2222222", summary="no match",
                project_key="HPC")),
        ]
        rules_data = [
            {"Project Key": "DO", "RuleID": "R001",
             "Rule Pattern": "CDFP fault", "Match Field": "summary",
             "Failure Category": "CDFP Fault", "Category": "CDFP",
             "Priority": "100", "Confidence": "0.95",
             "Created By": "human", "Hit Count": "0"},
        ]
        argv, output_dir = self._setup_env(
            tmp_path, tickets=tickets, rules_data=rules_data)
        with patch("sys.argv", ["rule_engine_categorize.py"] + argv):
            main()
        csv_path = output_dir / "tickets-categorized.csv"
        with open(csv_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        # DO ticket matches rule, HPC ticket doesn't (rule is DO-only)
        do_row = [r for r in rows if r["Ticket"] == "DO-1111111"][0]
        hpc_row = [r for r in rows if r["Ticket"] == "HPC-2222222"][0]
        assert do_row["Categorization Source"] == "rule"
        assert hpc_row["Categorization Source"] == "none"

    def test_runbook_stats(self, tmp_path, capsys):
        """Verify runbook count is printed in stats."""
        argv, output_dir = self._setup_env(tmp_path)
        with patch("sys.argv", ["rule_engine_categorize.py"] + argv):
            main()
        output = capsys.readouterr().out
        assert "Runbook=TRUE" in output
        assert "Rule matched" in output
        assert "No match" in output
