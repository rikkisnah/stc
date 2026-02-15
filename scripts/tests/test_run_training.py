# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted
"""Tests for run-training.py."""

import csv
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

run_training = importlib.import_module("run-training")
parse_args = run_training.parse_args
main = run_training.main


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

TICKET_HEADER = (
    "Project Key",
    "Ticket",
    "Ticket Description",
    "Category of Issue",
    "Category",
    "Human Audit for Accuracy",
    "Human Comments",
)


def _write_csv(path: Path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _run_main(*args):
    return main(list(args))


def test_parse_args_requires_all_required_flags():
    with pytest.raises(SystemExit):
        parse_args([])


def test_parse_args_requires_prompt_input():
    with pytest.raises(SystemExit):
        parse_args([
            "--tickets-categorized", "tickets.csv",
            "--rules-engine-file", "rules.csv",
        ])


def test_missing_required_inputs_fail_with_error(tmp_path):
    tickets = tmp_path / "tickets-categorized.csv"
    tickets.write_text("Ticket,Project Key\n")
    rules = tmp_path / "rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [])
    prompt = tmp_path / "prompt.md"
    prompt.write_text("prompt")

    with pytest.raises(SystemExit) as exc:
        main([
            "--tickets-categorized", str(tickets),
            "--rules-engine-file", str(rules),
            "--prompt", str(prompt),
            "--output-rule-engine", str(tmp_path / "out.csv"),
    ])
    assert "missing required columns" in str(exc.value)


def test_validate_file_enforces_exists(tmp_path):
    with pytest.raises(SystemExit) as exc:
        run_training.validate_file(tmp_path / "missing-rules.csv", "Rules engine")
    assert "Rules engine file not found" in str(exc.value)


def test_load_prompt_text_rejects_empty_inline_prompt():
    with pytest.raises(SystemExit) as exc:
        run_training.load_prompt_text("", None)
    assert "missing required prompt input" in str(exc.value)


def test_output_rule_engine_copied_and_source_file_unmodified(tmp_path, monkeypatch):
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(
        rules,
        RULE_HEADER,
        [{
            "Project Key": "DO",
            "RuleID": "R001",
            "Rule Pattern": "abc",
            "Match Field": "summary",
            "Failure Category": "CPU/Processor Fault",
            "Category": "CPU/Processor",
            "Priority": "80",
            "Confidence": "1",
            "Created By": "human",
            "Hit Count": "0",
        }],
    )

    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(tickets, TICKET_HEADER, [
        {
            "Project Key": "DO",
            "Ticket": "DO-111",
            "Ticket Description": "desc",
            "Category of Issue": "CPU/Processor",
            "Category": "CPU/Processor",
            "Human Audit for Accuracy": "incorrect",
            "Human Comments": "Need better rule",
        }
    ])

    prompt = tmp_path / "prompt.md"
    prompt.write_text("prompt")

    output = tmp_path / "rule-engine.local.csv"

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="{" + "\"proposals\": []}" )

    monkeypatch.setattr(run_training.subprocess, "run", fake_run)

    original_rules = rules.read_text(encoding="utf-8")
    _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--prompt",
        str(prompt),
        "--output-rule-engine",
        str(output),
    )

    assert output.exists()
    assert rules.read_text(encoding="utf-8") == original_rules


def test_call_codex_handles_timeout_and_failure(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise run_training.subprocess.TimeoutExpired(cmd=[run_training.CODEX_BIN], timeout=10)

    monkeypatch.setattr(run_training.subprocess, "run", raise_timeout)
    assert run_training.call_codex("prompt", [{"Ticket": "DO-100"}], 10) == []

    def fake_fail(cmd, **kwargs):
        return SimpleNamespace(returncode=1, stderr="failed", stdout="")

    monkeypatch.setattr(run_training.subprocess, "run", fake_fail)
    assert run_training.call_codex("prompt", [{"Ticket": "DO-100"}], 10) == []


def test_call_codex_validates_proposals_shape(monkeypatch):
    def fake_not_list(cmd, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stderr="",
            stdout=json.dumps({"proposals": {"items": []}}),
        )

    monkeypatch.setattr(run_training.subprocess, "run", fake_not_list)
    assert run_training.call_codex("prompt", [{"Ticket": "DO-100"}], 10) == []


def test_normalize_proposal_handles_empty_pattern_and_type_fallbacks():
    assert run_training.normalize_proposal({}, "", "R001") is None

    rule = run_training.normalize_proposal(
        {
            "Rule Pattern": "cpu.*",
            "Priority": "not-a-number",
            "Confidence": "not-a-number",
            "Hit Count": "not-a-number",
        },
        "DO",
        "R002",
    )

    assert rule["Priority"] == 80
    assert rule["Confidence"] == 1
    assert rule["Hit Count"] == 0


def test_determine_project_key_falls_back_to_single_project_mapping():
    assert (
        run_training.determine_project_key(
            {},
            {"DO-100": "DO"},
        )
        == "DO"
    )


def test_determine_project_key_prefers_explicit_project_key():
    assert (
        run_training.determine_project_key(
            {"Project Key": "DX"},
            {"DO-100": "DO"},
        )
        == "DX"
    )


def test_determine_project_key_returns_empty_when_unresolved():
    assert run_training.determine_project_key({}, {}) == ""


def test_only_incorrect_rows_sent_to_codex_and_missing_comments_skipped(tmp_path, monkeypatch):
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [{
        "Project Key": "DO",
        "RuleID": "R001",
        "Rule Pattern": "abc",
        "Match Field": "summary",
        "Failure Category": "CPU",
        "Category": "CPU/Processor",
        "Priority": "80",
        "Confidence": "1",
        "Created By": "human",
        "Hit Count": "0",
    }])

    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(
        tickets,
        TICKET_HEADER,
        [
            {
                "Project Key": "DO",
                "Ticket": "DO-111",
                "Ticket Description": "incorrect with comment",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "incorrect",
                "Human Comments": "bad classification",
            },
            {
                "Project Key": "DO",
                "Ticket": "DO-222",
                "Ticket Description": "incorrect without comment",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "incorrect",
                "Human Comments": "",
            },
            {
                "Project Key": "DO",
                "Ticket": "DO-333",
                "Ticket Description": "correct row",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "correct",
                "Human Comments": "not used",
            },
        ],
    )

    prompt = tmp_path / "prompt.md"
    prompt.write_text("prompt")

    output = tmp_path / "rule-engine.local.csv"

    captured_input = {}

    def fake_run(cmd, input, text, capture_output, **kwargs):
        captured_input["cmd"] = cmd
        captured_input["input"] = input
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "proposals": [
                    {
                        "Ticket": "DO-111",
                        "Rule Pattern": "cpu_fault",
                        "Match Field": "summary",
                        "Failure Category": "CPU mismatch",
                        "Category": "CPU/Processor",
                        "Priority": 80,
                        "Confidence": 1,
                        "Created By": "human-feedback",
                        "Hit Count": 1,
                    }
                ],
            }),
            stderr="",
        )

    monkeypatch.setattr(run_training.subprocess, "run", fake_run)

    _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--prompt",
        str(prompt),
        "--output-rule-engine",
        str(output),
    )

    assert "-p" in captured_input["cmd"]
    assert "plan" in captured_input["cmd"]

    payload_json = captured_input["input"].split("INPUT JSON:\n", 1)[1]
    parsed = json.loads(payload_json)
    tickets_in_payload = [row["Ticket"] for row in parsed["feedback_rows"]]
    assert "DO-111" in tickets_in_payload
    assert "DO-222" not in tickets_in_payload
    assert "DO-333" not in tickets_in_payload

    with open(output, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[1]["Project Key"] == "DO"
    assert rows[1]["Rule Pattern"] == "cpu_fault"
    assert rows[1]["RuleID"] == "R002"


def test_sequential_rule_ids_are_appended_from_existing_high_watermark(tmp_path, monkeypatch):
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [
        {
            "Project Key": "DO",
            "RuleID": "R001",
            "Rule Pattern": "abc",
            "Match Field": "summary",
            "Failure Category": "CPU/Processor Fault",
            "Category": "CPU/Processor",
            "Priority": "80",
            "Confidence": "1",
            "Created By": "human",
            "Hit Count": "0",
        },
        {
            "Project Key": "DO",
            "RuleID": "R010",
            "Rule Pattern": "xyz",
            "Match Field": "summary",
            "Failure Category": "GPU Fault",
            "Category": "GPU",
            "Priority": "80",
            "Confidence": "1",
            "Created By": "human",
            "Hit Count": "0",
        },
    ])

    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(tickets, TICKET_HEADER, [
        {
            "Project Key": "DO",
            "Ticket": "DO-100",
            "Ticket Description": "bad row",
            "Category of Issue": "CPU",
            "Category": "CPU/Processor",
            "Human Audit for Accuracy": "incorrect",
            "Human Comments": "notes",
        },
    ])

    prompt = tmp_path / "prompt.md"
    prompt.write_text("prompt")

    output = tmp_path / "rule-engine.local.csv"

    def fake_run(cmd, input, text, capture_output, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "proposals": [
                    {
                        "Ticket": "DO-100",
                        "Rule Pattern": "bad",
                        "Match Field": "summary",
                        "Failure Category": "CPU mismatch",
                        "Category": "CPU/Processor",
                    },
                    {
                        "Ticket": "DO-100",
                        "Rule Pattern": "fault",
                        "Match Field": "description",
                        "Failure Category": "CPU mismatch",
                        "Category": "CPU/Processor",
                    },
                ],
            }),
            stderr="",
        )

    monkeypatch.setattr(run_training.subprocess, "run", fake_run)

    _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--prompt",
        str(prompt),
        "--output-rule-engine",
        str(output),
    )

    with open(output, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 4
    assert rows[2]["RuleID"] == "R011"
    assert rows[3]["RuleID"] == "R012"


def test_main_skips_non_dict_proposals(tmp_path, monkeypatch):
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [{
        "Project Key": "DO",
        "RuleID": "R001",
        "Rule Pattern": "abc",
        "Match Field": "summary",
        "Failure Category": "CPU/Processor Fault",
        "Category": "CPU/Processor",
        "Priority": "80",
        "Confidence": "1",
        "Created By": "human",
        "Hit Count": "0",
    }])

    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(tickets, TICKET_HEADER, [
        {
            "Project Key": "DO",
            "Ticket": "DO-100",
            "Ticket Description": "bad row",
            "Category of Issue": "CPU",
            "Category": "CPU/Processor",
            "Human Audit for Accuracy": "incorrect",
            "Human Comments": "notes",
        },
    ])

    prompt = tmp_path / "prompt.md"
    prompt.write_text("prompt")

    output = tmp_path / "rule-engine.local.csv"

    def fake_run(cmd, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "proposals": [
                    "bad-proposal",
                    {
                        "Ticket": "DO-100",
                        "Rule Pattern": "good",
                        "Match Field": "summary",
                        "Failure Category": "CPU",
                        "Category": "CPU/Processor",
                    },
                ],
            }),
            stderr="",
        )

    monkeypatch.setattr(run_training.subprocess, "run", fake_run)
    _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--prompt",
        str(prompt),
        "--output-rule-engine",
        str(output),
    )

    with open(output, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[1]["Rule Pattern"] == "good"


def test_invalid_json_and_invalid_regex_do_not_corrupt_output(tmp_path, monkeypatch):
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [
        {
            "Project Key": "DO",
            "RuleID": "R001",
            "Rule Pattern": "abc",
            "Match Field": "summary",
            "Failure Category": "CPU/Processor Fault",
            "Category": "CPU/Processor",
            "Priority": "80",
            "Confidence": "1",
            "Created By": "human",
            "Hit Count": "0",
        },
    ])

    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(tickets, TICKET_HEADER, [
        {
            "Project Key": "DO",
            "Ticket": "DO-100",
            "Ticket Description": "bad row",
            "Category of Issue": "CPU",
            "Category": "CPU/Processor",
            "Human Audit for Accuracy": "incorrect",
            "Human Comments": "needs correction",
        },
    ])

    prompt = tmp_path / "prompt.md"
    prompt.write_text("prompt")

    output = tmp_path / "rule-engine.local.csv"

    call = {"count": 0}

    def fake_run_invalid_json(cmd, input, text, capture_output, **kwargs):
        call["count"] += 1
        return SimpleNamespace(returncode=0, stdout="{invalid-json}", stderr="")

    monkeypatch.setattr(run_training.subprocess, "run", fake_run_invalid_json)
    _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--prompt",
        str(prompt),
        "--output-rule-engine",
        str(output),
    )

    with open(output, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["RuleID"] == "R001"
    assert call["count"] == 1

    def fake_run_invalid_regex(cmd, input, text, capture_output, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "proposals": [
                    {
                        "Ticket": "DO-100",
                        "Rule Pattern": "[",
                        "Match Field": "summary",
                        "Failure Category": "Bad regex",
                        "Category": "CPU/Processor",
                    },
                    {
                        "Ticket": "DO-100",
                        "Rule Pattern": "good",
                        "Match Field": "summary",
                        "Failure Category": "Good regex",
                        "Category": "CPU/Processor",
                    },
                ],
            }),
            stderr="",
        )

    monkeypatch.setattr(run_training.subprocess, "run", fake_run_invalid_regex)
    _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--prompt",
        str(prompt),
        "--output-rule-engine",
        str(output),
    )

    with open(output, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[1]["Rule Pattern"] == "good"


def test_call_codex_skips_when_no_rows(tmp_path, monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called when rows are empty")

    monkeypatch.setattr(run_training.subprocess, "run", fail_if_called)
    assert run_training.call_codex("prompt", [], 10) == []


def test_append_rules_noop_for_empty_proposal_list(tmp_path):
    output = tmp_path / "rules.csv"
    output.write_text("header\n")

    run_training.append_rules(output, [])

    assert output.read_text(encoding="utf-8") == "header\n"

def test_prompt_is_loaded_from_cli_or_markdown_file(tmp_path, monkeypatch):
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [])

    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(
        tickets,
        TICKET_HEADER,
        [
            {
                "Project Key": "DO",
                "Ticket": "DO-100",
                "Ticket Description": "bad row",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "incorrect",
                "Human Comments": "needs correction",
            },
        ],
    )

    output_inline = tmp_path / "rule-engine-inline.csv"
    observed = {}

    def fake_run(cmd, input, text, capture_output, **kwargs):
        observed["payload"] = input
        return SimpleNamespace(returncode=0, stdout='{"proposals": []}', stderr="")

    monkeypatch.setattr(run_training.subprocess, "run", fake_run)

    _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--prompt",
        "inline prompt text",
        "--output-rule-engine",
        str(output_inline),
    )
    assert observed["payload"].startswith("inline prompt text\n\nINPUT JSON:")

    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("markdown prompt text")
    output_markdown = tmp_path / "rule-engine-markdown.csv"

    observed = {}
    _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--prompt-file",
        str(prompt_file),
        "--output-rule-engine",
        str(output_markdown),
    )
    assert observed["payload"].startswith("markdown prompt text\n\nINPUT JSON:")
