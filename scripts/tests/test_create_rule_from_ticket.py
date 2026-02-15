# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted
"""Tests for create_rule_from_ticket.py."""

import csv
import json
from pathlib import Path

import pytest

import create_rule_from_ticket


RULE_HEADER = (
    "Project Key",
    "RuleID",
    "Rule Pattern",
    "Match Field",
    "Failure Category",
    "Category",
    "Priority",
    "Confidence",
    "Created By",
    "Hit Count",
)


def _write_rules(path: Path, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RULE_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def _read_rules(path: Path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _make_prompt_inputs(*values):
    iterator = iter(values)
    return lambda _prompt="": next(iterator)


def test_parse_args_defaults():
    args = create_rule_from_ticket.parse_args([])
    assert args.match_field_default == "summary+description"
    assert args.created_by == "human-feedback"
    assert args.priority == 85
    assert args.confidence == 1.0
    assert args.hit_count == 0


def test_validate_ticket_key_rejects_invalid():
    with pytest.raises(SystemExit, match="Invalid ticket key"):
        create_rule_from_ticket.validate_ticket_key("invalid")


def test_find_normalized_ticket_uses_latest_date_folder(tmp_path):
    root = tmp_path / "normalized-tickets"
    older = root / "2026-02-14" / "HPC-100001.json"
    newer = root / "2026-02-15" / "HPC-100001.json"
    _write_json(older, {"ticket": {"summary": "older"}})
    _write_json(newer, {"ticket": {"summary": "newer"}})

    picked = create_rule_from_ticket.find_normalized_ticket(root, "HPC-100001")
    assert picked == newer


def test_find_normalized_ticket_exits_when_missing(tmp_path):
    with pytest.raises(SystemExit, match="not found in normalized-tickets"):
        create_rule_from_ticket.find_normalized_ticket(tmp_path / "normalized-tickets", "HPC-1")


def test_build_rule_pattern_token_and_fallback_paths():
    token_pattern = create_rule_from_ticket.build_rule_pattern(
        "Cable validation failure on node", "I think this is cable validation", "HPC-111111"
    )
    assert "cable" in token_pattern

    fallback_pattern = create_rule_from_ticket.build_rule_pattern("!!", "??", "HPC-111111")
    assert fallback_pattern == "HPC\\-111111"


def test_load_ticket_json_exits_on_bad_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not-json", encoding="utf-8")
    with pytest.raises(SystemExit, match="Failed to parse"):
        create_rule_from_ticket.load_ticket_json(bad, "normalized")


def test_load_ticket_json_exits_when_file_missing(tmp_path):
    with pytest.raises(SystemExit, match="not found"):
        create_rule_from_ticket.load_ticket_json(tmp_path / "missing.json", "normalized")


def test_load_rules_engine_rejects_missing_columns(tmp_path):
    bad = tmp_path / "rule-engine.local.csv"
    bad.write_text("RuleID,Rule Pattern\nR001,a\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="missing required columns"):
        create_rule_from_ticket.load_rules_engine(bad)


def test_load_rules_engine_rejects_missing_file(tmp_path):
    with pytest.raises(SystemExit, match="file not found"):
        create_rule_from_ticket.load_rules_engine(tmp_path / "missing.csv")


def test_load_rules_engine_rejects_empty_csv(tmp_path):
    empty = tmp_path / "rule-engine.local.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit, match="empty or missing headers"):
        create_rule_from_ticket.load_rules_engine(empty)


def test_prompt_required_retries_until_non_empty():
    value = create_rule_from_ticket.prompt_required(
        "Value", input_fn=_make_prompt_inputs("", "   ", "ok"), print_fn=lambda *_: None
    )
    assert value == "ok"


def test_infer_project_key_falls_back_to_ticket_prefix():
    project = create_rule_from_ticket.infer_project_key("HPC-100001", {"ticket": {"project": {}}})
    assert project == "HPC"


def test_infer_project_key_can_return_empty():
    project = create_rule_from_ticket.infer_project_key("NOSEP", {"ticket": {"project": {}}})
    assert project == ""


def test_build_rule_pattern_single_token_branch():
    pattern = create_rule_from_ticket.build_rule_pattern("network", "the and or", "DO-1")
    assert pattern == "network"


def test_main_appends_rule_when_confirmed(tmp_path):
    ticket_key = "HPC-100001"

    ticket_json_dir = tmp_path / "tickets-json"
    _write_json(ticket_json_dir / f"{ticket_key}.json", {"key": ticket_key})

    normalized_root = tmp_path / "normalized-tickets"
    _write_json(
        normalized_root / "2026-02-15" / f"{ticket_key}.json",
        {"ticket": {"summary": "cable validation failed", "project": {"key": "HPC"}}},
    )

    rules_path = tmp_path / "rule-engine.local.csv"
    _write_rules(
        rules_path,
        [
            {
                "Project Key": "HPC",
                "RuleID": "R009",
                "Rule Pattern": "old",
                "Match Field": "summary",
                "Failure Category": "Old",
                "Category": "Old",
                "Priority": "80",
                "Confidence": "1",
                "Created By": "human",
                "Hit Count": "0",
            }
        ],
    )

    result = create_rule_from_ticket.main(
        [
            "--ticket-json-dir",
            str(ticket_json_dir),
            "--normalized-root",
            str(normalized_root),
            "--rules-engine",
            str(rules_path),
        ],
        input_fn=_make_prompt_inputs(
            ticket_key,
            "this ticket repeatedly fails cable validation on boot",
            "CDFP Cable Validation Failure",
            "CDFP",
            "",
            "",
            "y",
        ),
        print_fn=lambda *_: None,
    )
    assert result == 0

    rows = _read_rules(rules_path)
    assert len(rows) == 2
    assert rows[-1]["RuleID"] == "R010"
    assert rows[-1]["Project Key"] == "HPC"
    assert rows[-1]["Failure Category"] == "CDFP Cable Validation Failure"
    assert rows[-1]["Category"] == "CDFP"
    assert rows[-1]["Created By"] == "human-feedback"


def test_run_interactive_does_not_append_when_declined(tmp_path):
    ticket_key = "DO-200001"
    ticket_json_dir = tmp_path / "tickets-json"
    _write_json(ticket_json_dir / f"{ticket_key}.json", {"key": ticket_key})

    normalized_root = tmp_path / "normalized-tickets"
    _write_json(
        normalized_root / "2026-02-15" / f"{ticket_key}.json",
        {"ticket": {"summary": "network timeout", "project": {"key": "DO"}}},
    )

    rules_path = tmp_path / "rule-engine.local.csv"
    _write_rules(rules_path, [])

    args = create_rule_from_ticket.parse_args(
        [
            "--ticket-json-dir",
            str(ticket_json_dir),
            "--normalized-root",
            str(normalized_root),
            "--rules-engine",
            str(rules_path),
        ]
    )

    result = create_rule_from_ticket.run_interactive(
        args,
        input_fn=_make_prompt_inputs(
            ticket_key,
            "new networking failure family",
            "Network Timeout",
            "Networking",
            "description",
            "network.*timeout",
            "n",
        ),
        print_fn=lambda *_: None,
    )
    assert result == 1
    assert _read_rules(rules_path) == []


def test_run_interactive_requires_raw_ticket_json(tmp_path):
    ticket_key = "HPC-300001"
    normalized_root = tmp_path / "normalized-tickets"
    _write_json(
        normalized_root / "2026-02-15" / f"{ticket_key}.json",
        {"ticket": {"summary": "exists in normalized"}},
    )
    rules_path = tmp_path / "rule-engine.local.csv"
    _write_rules(rules_path, [])

    args = create_rule_from_ticket.parse_args(
        [
            "--ticket-json-dir",
            str(tmp_path / "tickets-json"),
            "--normalized-root",
            str(normalized_root),
            "--rules-engine",
            str(rules_path),
        ]
    )
    with pytest.raises(SystemExit, match="not found in tickets-json"):
        create_rule_from_ticket.run_interactive(
            args,
            input_fn=_make_prompt_inputs(ticket_key),
            print_fn=lambda *_: None,
        )
