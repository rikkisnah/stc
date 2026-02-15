# Code was generated via OCI AI and was reviewed by a human SDE
# Tag: #ai-assisted
"""Tests for run_training.py."""

import csv
import importlib
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

run_training = importlib.import_module("run_training")
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
    argv = list(args)
    if "--yes" not in argv and "-y" not in argv:
        argv.append("--yes")
    return main(argv)


def test_parse_args_requires_all_required_flags():
    with pytest.raises(SystemExit):
        parse_args([])


def test_parse_args_requires_prompt_input():
    with pytest.raises(SystemExit):
        parse_args([
            "--tickets-categorized", "tickets.csv",
            "--rules-engine-file", "rules.csv",
        ])


def test_parse_args_defaults():
    args = parse_args([
        "--tickets-categorized", "tickets.csv",
        "--rules-engine-file", "rules.csv",
        "--prompt", "inline prompt",
    ])
    assert args.max_review_rows == 200
    assert args.codex_batch_size == 2
    assert args.codex_timeout == 120
    assert args.yes is False


def test_parse_args_rejects_non_positive_max_review_rows():
    with pytest.raises(SystemExit):
        parse_args([
            "--tickets-categorized", "tickets.csv",
            "--rules-engine-file", "rules.csv",
            "--prompt", "inline prompt",
            "--max-review-rows", "0",
        ])


def test_parse_args_accepts_legacy_max_incorrect_rows_alias():
    args = parse_args([
        "--tickets-categorized", "tickets.csv",
        "--rules-engine-file", "rules.csv",
        "--prompt", "inline prompt",
        "--max-incorrect-rows", "2",
    ])
    assert args.max_review_rows == 2


def test_resolve_log_file_path_defaults_to_timestamped_logs_dir():
    started_at = run_training.datetime(2026, 2, 15, 6, 0, 0, tzinfo=run_training.timezone.utc)
    path = run_training.resolve_log_file_path(None, started_at)
    assert str(path).endswith("scripts/logs/run_training_20260215T060000Z.log")


def test_resolve_log_file_path_respects_explicit_override(tmp_path):
    explicit = tmp_path / "custom.log"
    started_at = run_training.datetime(2026, 2, 15, 6, 0, 0, tzinfo=run_training.timezone.utc)
    path = run_training.resolve_log_file_path(explicit, started_at)
    assert path == explicit


def test_format_duration_hms():
    assert run_training._format_duration(0) == "0h 00m 00s"  # pylint: disable=protected-access
    assert run_training._format_duration(3661) == "1h 01m 01s"  # pylint: disable=protected-access


def test_estimate_runtime_seconds():
    estimated, worst, batches = run_training.estimate_runtime_seconds(900, 2, 60)
    assert estimated == 20250
    assert worst == 27000
    assert batches == 450
    estimated_zero, worst_zero, batches_zero = run_training.estimate_runtime_seconds(0, 2, 60)
    assert estimated_zero == 0
    assert worst_zero is None
    assert batches_zero == 0


def test_confirm_ready_to_run_accepts_yes(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: "yes")
    assert run_training.confirm_ready_to_run(30, 60, 2) is True


def test_confirm_ready_to_run_rejects_default(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: "")
    assert run_training.confirm_ready_to_run(30, None, 2) is False


def test_parse_args_rejects_non_positive_codex_batch_size():
    with pytest.raises(SystemExit):
        parse_args([
            "--tickets-categorized", "tickets.csv",
            "--rules-engine-file", "rules.csv",
            "--prompt", "inline prompt",
            "--codex-batch-size", "0",
        ])


def test_parse_args_ml_requires_model_and_category_map():
    with pytest.raises(SystemExit):
        parse_args([
            "--tickets-categorized", "tickets.csv",
            "--rules-engine-file", "rules.csv",
            "--engine", "ml",
        ])

    with pytest.raises(SystemExit):
        parse_args([
            "--tickets-categorized", "tickets.csv",
            "--rules-engine-file", "rules.csv",
            "--engine", "ml",
            "--ml-model", "model.joblib",
        ])


def test_parse_args_ml_accepts_model_and_category_map():
    args = parse_args([
        "--tickets-categorized", "tickets.csv",
        "--rules-engine-file", "rules.csv",
        "--engine", "ml",
        "--ml-model", "model.joblib",
        "--ml-category-map", "category_map.json",
    ])
    assert args.engine == "ml"
    assert str(args.ml_model) == "model.joblib"
    assert str(args.ml_category_map) == "category_map.json"


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
        "--max-review-rows",
        "2",
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


def test_main_cancels_when_user_not_ready(tmp_path, monkeypatch):
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [])
    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(tickets, TICKET_HEADER, [
        {
            "Project Key": "DO",
            "Ticket": "DO-100",
            "Ticket Description": "desc",
            "Category of Issue": "CPU",
            "Category": "CPU/Processor",
            "Human Audit for Accuracy": "needs-review",
            "Human Comments": "",
        }
    ])
    prompt = tmp_path / "prompt.md"
    prompt.write_text("prompt")
    output = tmp_path / "rule-engine.local.csv"

    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: "n")
    result = main([
        "--tickets-categorized", str(tickets),
        "--rules-engine-file", str(rules),
        "--prompt", str(prompt),
        "--output-rule-engine", str(output),
    ])
    assert result["rules_added"] == 0


def test_call_codex_validates_proposals_shape(monkeypatch):
    def fake_not_list(cmd, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stderr="",
            stdout=json.dumps({"proposals": {"items": []}}),
        )

    monkeypatch.setattr(run_training.subprocess, "run", fake_not_list)
    assert run_training.call_codex("prompt", [{"Ticket": "DO-100"}], 10) == []


def test_call_codex_parses_json_from_fenced_block(monkeypatch):
    def fake_fenced_json(cmd, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stderr="",
            stdout="Here are proposals:\n```json\n{\"proposals\":[{\"Rule Pattern\":\"cpu\",\"Match Field\":\"summary\"}]}\n```",
        )

    monkeypatch.setattr(run_training.subprocess, "run", fake_fenced_json)
    proposals = run_training.call_codex("prompt", [{"Ticket": "DO-100"}], 10)
    assert isinstance(proposals, list)
    assert proposals[0]["Rule Pattern"] == "cpu"


def test_call_codex_parses_json_embedded_in_prose(monkeypatch):
    def fake_embedded_json(cmd, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stderr="",
            stdout='Plan complete. {"proposals":[{"Rule Pattern":"mem","Match Field":"description"}]} End.',
        )

    monkeypatch.setattr(run_training.subprocess, "run", fake_embedded_json)
    proposals = run_training.call_codex("prompt", [{"Ticket": "DO-100"}], 10)
    assert isinstance(proposals, list)
    assert proposals[0]["Rule Pattern"] == "mem"


def test_parse_codex_json_output_empty_text_returns_none():
    assert run_training._parse_codex_json_output("") is None


def test_parse_codex_json_output_skips_bad_fenced_then_uses_good_fenced():
    text = (
        "```json\n{bad json}\n```\n"
        "```json\n{\"proposals\": []}\n```"
    )
    parsed = run_training._parse_codex_json_output(text)
    assert parsed == {"proposals": []}


def test_parse_codex_json_output_no_json_object_returns_none():
    assert run_training._parse_codex_json_output("plain prose only") is None


def test_call_codex_emits_heartbeat(monkeypatch, capsys):
    original_interval = run_training.HEARTBEAT_INTERVAL_SEC
    monkeypatch.setattr(run_training, "HEARTBEAT_INTERVAL_SEC", 0.01)

    def fake_run(cmd, **kwargs):
        time.sleep(0.03)
        return SimpleNamespace(returncode=0, stderr="", stdout='{"proposals": []}')

    monkeypatch.setattr(run_training.subprocess, "run", fake_run)
    assert run_training.call_codex("prompt", [{"Ticket": "DO-100"}], 10) == []
    out = capsys.readouterr().out
    assert "Heartbeat: Codex still running" in out
    monkeypatch.setattr(run_training, "HEARTBEAT_INTERVAL_SEC", original_interval)


def test_call_codex_prints_stderr_preview_on_invalid_json(monkeypatch, capsys):
    def fake_bad_json(cmd, **kwargs):
        return SimpleNamespace(returncode=0, stdout="not json", stderr="stderr details")

    monkeypatch.setattr(run_training.subprocess, "run", fake_bad_json)
    assert run_training.call_codex("prompt", [{"Ticket": "DO-100"}], 10) == []
    err = capsys.readouterr().err
    assert "Codex stderr preview" in err
    assert "stderr details" in err


def test_call_codex_with_reason_reports_invalid_json(monkeypatch):
    def fake_bad_json(cmd, **kwargs):
        return SimpleNamespace(returncode=0, stdout="not json", stderr="")

    monkeypatch.setattr(run_training.subprocess, "run", fake_bad_json)
    proposals, reason = run_training._call_codex_with_reason(  # pylint: disable=protected-access
        "prompt", [{"Ticket": "DO-100"}], 10
    )
    assert proposals == []
    assert reason == "invalid_json"


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


def test_build_failure_to_category_map_skips_unknown_and_keeps_first():
    mapping = run_training.build_failure_to_category_map(
        [
            {
                "Project Key": "HPC",
                "Failure Category": "Power Event",
                "Category": "Power",
            },
            {
                "Project Key": "HPC",
                "Failure Category": "Power Event",
                "Category": "Power-Override",
            },
            {
                "Project Key": "HPC",
                "Failure Category": "Unknown",
                "Category": "unknown",
            },
        ]
    )
    assert mapping[("hpc", "power event")] == "Power"
    assert ("hpc", "unknown") not in mapping


def test_infer_category_from_failure_prefers_project_then_global():
    mapping = {
        ("hpc", "power event"): "Power-HPC",
        ("", "power event"): "Power-Global",
    }
    assert (
        run_training.infer_category_from_failure("HPC", "Power Event", mapping)
        == "Power-HPC"
    )
    assert (
        run_training.infer_category_from_failure("DO", "Power Event", mapping)
        == "Power-Global"
    )


def test_infer_category_from_failure_returns_none_for_empty_failure():
    assert run_training.infer_category_from_failure("HPC", "", {}) is None


def test_normalize_proposal_infers_category_from_failure_mapping():
    rule = run_training.normalize_proposal(
        {
            "Rule Pattern": "power.*",
            "Failure Category": "Potential Test Issue - Power Outage",
            "Category": "unknown",
        },
        "HPC",
        "R010",
        failure_to_category={
            (
                "hpc",
                "potential test issue - power outage",
            ): "Power"
        },
    )
    assert rule is not None
    assert rule["Category"] == "Power"


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


def test_load_feedback_rows_filters_to_incorrect_and_needs_review(tmp_path):
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
                "Ticket Description": "needs-review with comment",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "needs-review",
                "Human Comments": "needs triage",
            },
            {
                "Project Key": "DO",
                "Ticket": "DO-333",
                "Ticket Description": "correct row",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "correct",
                "Human Comments": "ignore",
            },
        ],
    )

    all_rows, review_rows, skipped = run_training.load_feedback_rows(tickets)
    assert len(all_rows) == 3
    assert [row["Ticket"] for row in review_rows] == ["DO-111", "DO-222"]
    assert skipped == 0


def test_review_rows_sent_to_codex_and_missing_comments_included(tmp_path, monkeypatch):
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
                "Ticket Description": "needs-review without comment",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "needs-review",
                "Human Comments": "",
            },
            {
                "Project Key": "DO",
                "Ticket": "DO-333",
                "Ticket Description": "needs-review with comment",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "needs-review",
                "Human Comments": "needs triage",
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
                    },
                    {
                        "Ticket": "DO-222",
                        "Rule Pattern": "triage_pattern",
                        "Match Field": "description+comments",
                        "Failure Category": "Unknown",
                        "Category": "unknown",
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
        "--max-review-rows",
        "2",
        "--output-rule-engine",
        str(output),
    )

    assert "-p" in captured_input["cmd"]
    assert "plan" in captured_input["cmd"]

    payload_json = captured_input["input"].split("INPUT JSON:\n", 1)[1]
    parsed = json.loads(payload_json)
    tickets_in_payload = [row["Ticket"] for row in parsed["feedback_rows"]]
    assert "DO-111" in tickets_in_payload
    assert "DO-222" in tickets_in_payload
    assert "DO-333" not in tickets_in_payload

    with open(output, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    assert rows[1]["Project Key"] == "DO"
    assert rows[1]["Rule Pattern"] == "cpu_fault"
    assert rows[1]["RuleID"] == "R002"
    assert rows[2]["Rule Pattern"] == "triage_pattern"
    assert rows[2]["RuleID"] == "R003"


def test_max_review_rows_limits_payload_to_one(tmp_path, monkeypatch):
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [])

    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(
        tickets,
        TICKET_HEADER,
        [
            {
                "Project Key": "DO",
                "Ticket": "DO-111",
                "Ticket Description": "row 1",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "incorrect",
                "Human Comments": "bad 1",
            },
            {
                "Project Key": "DO",
                "Ticket": "DO-222",
                "Ticket Description": "row 2",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "incorrect",
                "Human Comments": "bad 2",
            },
            {
                "Project Key": "DO",
                "Ticket": "DO-333",
                "Ticket Description": "row 3",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "incorrect",
                "Human Comments": "bad 3",
            },
        ],
    )

    output = tmp_path / "rule-engine.local.csv"
    captured_input = {}

    def fake_run(cmd, input, text, capture_output, **kwargs):
        captured_input["input"] = input
        return SimpleNamespace(returncode=0, stdout='{"proposals": []}', stderr="")

    monkeypatch.setattr(run_training.subprocess, "run", fake_run)

    _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--prompt",
        "inline prompt text",
        "--max-review-rows",
        "1",
        "--output-rule-engine",
        str(output),
    )

    payload_json = captured_input["input"].split("INPUT JSON:\n", 1)[1]
    parsed = json.loads(payload_json)
    tickets_in_payload = [row["Ticket"] for row in parsed["feedback_rows"]]
    assert tickets_in_payload == ["DO-111"]


def test_main_batches_codex_calls_by_batch_size(tmp_path, monkeypatch):
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [])

    tickets = tmp_path / "tickets-categorized.csv"
    rows = []
    for i in range(1, 8):
        rows.append({
            "Project Key": "DO",
            "Ticket": f"DO-{100+i}",
            "Ticket Description": f"row {i}",
            "Category of Issue": "CPU",
            "Category": "CPU/Processor",
            "Human Audit for Accuracy": "needs-review",
            "Human Comments": "",
        })
    _write_csv(tickets, TICKET_HEADER, rows)

    output = tmp_path / "rule-engine.local.csv"
    calls = {"count": 0}

    def fake_run(cmd, input, text, capture_output, **kwargs):
        calls["count"] += 1
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
        str(output),
        "--max-review-rows",
        "7",
        "--codex-batch-size",
        "3",
    )
    assert calls["count"] == 3


def test_load_feedback_rows_counts_missing_comments_but_keeps_rows(tmp_path):
    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(
        tickets,
        TICKET_HEADER,
        [
            {
                "Project Key": "DO",
                "Ticket": "DO-100",
                "Ticket Description": "needs review no comments",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "needs-review",
                "Human Comments": "",
            },
            {
                "Project Key": "DO",
                "Ticket": "DO-101",
                "Ticket Description": "incorrect with comments",
                "Category of Issue": "CPU",
                "Category": "CPU/Processor",
                "Human Audit for Accuracy": "incorrect",
                "Human Comments": "fix me",
            },
        ],
    )

    all_rows, review_rows, missing_comments = run_training.load_feedback_rows(tickets)
    assert len(all_rows) == 2
    assert [row["Ticket"] for row in review_rows] == ["DO-100", "DO-101"]
    assert missing_comments == 1


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


def test_main_infers_unknown_category_from_existing_failure_mapping(tmp_path, monkeypatch):
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [
        {
            "Project Key": "HPC",
            "RuleID": "R001",
            "Rule Pattern": "existing",
            "Match Field": "comments",
            "Failure Category": "Potential Test Issue - Power Outage",
            "Category": "Power",
            "Priority": "80",
            "Confidence": "1",
            "Created By": "human",
            "Hit Count": "0",
        },
    ])

    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(tickets, TICKET_HEADER, [
        {
            "Project Key": "HPC",
            "Ticket": "HPC-100",
            "Ticket Description": "power event case",
            "Category of Issue": "uncategorized",
            "Category": "unknown",
            "Human Audit for Accuracy": "needs-review",
            "Human Comments": "",
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
                    {
                        "Ticket": "HPC-100",
                        "Rule Pattern": "power outage",
                        "Match Field": "comments",
                        "Failure Category": "Potential Test Issue - Power Outage",
                        "Category": "unknown",
                    },
                ]
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
    assert rows[1]["Failure Category"] == "Potential Test Issue - Power Outage"
    assert rows[1]["Category"] == "Power"


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


def test_find_latest_tickets_dir_returns_none_when_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(run_training, "REPO_ROOT", tmp_path)
    assert run_training.find_latest_tickets_dir() is None


def test_find_latest_tickets_dir_returns_latest_date(monkeypatch, tmp_path):
    root = tmp_path / "scripts" / "normalized-tickets"
    (root / "2026-02-14").mkdir(parents=True)
    (root / "2026-02-15").mkdir(parents=True)
    monkeypatch.setattr(run_training, "REPO_ROOT", tmp_path)
    assert run_training.find_latest_tickets_dir() == (root / "2026-02-15")


def test_load_ticket_jsons_returns_empty_for_invalid_dir(tmp_path):
    loaded = run_training._load_ticket_jsons(tmp_path / "missing", {"HPC-1"})  # pylint: disable=protected-access
    assert loaded == {}


def test_load_ticket_jsons_filters_by_ticket_key(tmp_path):
    tickets_dir = tmp_path / "normalized"
    tickets_dir.mkdir()
    (tickets_dir / "HPC-1.json").write_text('{"ticket":{"summary":"one"}}', encoding="utf-8")
    (tickets_dir / "HPC-2.json").write_text('{"ticket":{"summary":"two"}}', encoding="utf-8")
    loaded = run_training._load_ticket_jsons(tickets_dir, {"HPC-2"})  # pylint: disable=protected-access
    assert list(loaded.keys()) == ["HPC-2"]


class _ProbVector(list):
    def argmax(self):
        return max(range(len(self)), key=lambda idx: self[idx])


class _FakePipeline:
    classes_ = ["COI_A", "COI_B"]

    def __init__(self, probabilities):
        self._probabilities = probabilities

    def predict_proba(self, texts):
        text = texts[0]
        return [_ProbVector(self._probabilities[text])]


class _TruthyEmptyTerms:
    def __bool__(self):
        return True

    def __iter__(self):
        return iter(())

    def __getitem__(self, _item):
        return []


def test_generate_ml_proposals_returns_empty_without_ticket_jsons(monkeypatch, tmp_path):
    fake_ml_module = SimpleNamespace(
        build_feature_text=lambda ticket: ticket.get("feature", ""),
        extract_top_terms=lambda _pipeline, _text, n=5: [("term", 1.0)][:n],
        ML_CONFIDENCE_THRESHOLD=0.5,
    )
    monkeypatch.setitem(sys.modules, "ml_classifier", fake_ml_module)

    pipeline = _FakePipeline({"x": [0.9, 0.1]})
    proposals = run_training.generate_ml_proposals(
        [{"Ticket": "HPC-1", "Project Key": "HPC"}],
        pipeline,
        {"COI_A": "CategoryA"},
        tmp_path / "missing",
    )
    assert proposals == []


def test_generate_ml_proposals_covers_skip_and_success_paths(monkeypatch, tmp_path):
    def fake_extract_top_terms(_pipeline, text, n=5):
        if text == "no_terms":
            return []
        if text == "pattern_empty":
            return _TruthyEmptyTerms()
        if text == "two_terms":
            return [("cable", 1.0), ("i2c", 0.9), ("extra", 0.1)][:n]
        if text == "one_term":
            return [("network", 0.8)][:n]
        return [("other", 1.0)][:n]

    fake_ml_module = SimpleNamespace(
        build_feature_text=lambda ticket: ticket.get("feature", ""),
        extract_top_terms=fake_extract_top_terms,
        ML_CONFIDENCE_THRESHOLD=0.5,
    )
    monkeypatch.setitem(sys.modules, "ml_classifier", fake_ml_module)

    tickets_dir = tmp_path / "normalized"
    tickets_dir.mkdir()
    ticket_payloads = {
        "HPC-EMPTY": {"feature": "", "ticket": {"summary": "empty"}},
        "HPC-LOW": {"feature": "low_conf", "ticket": {"summary": "low conf"}},
        "HPC-NO-TERMS": {"feature": "no_terms", "ticket": {"summary": "term miss"}},
        "HPC-PATTERN-EMPTY": {"feature": "pattern_empty", "ticket": {"summary": "term miss"}},
        "HPC-TWO": {"feature": "two_terms", "ticket": {"summary": "cable i2c timeout"}},
        "HPC-ONE": {"feature": "one_term", "ticket": {"summary": "packet loss"}},
        "HPC-OTHER": {"feature": "other_case", "ticket": {"summary": "misc issue"}},
    }
    for key, payload in ticket_payloads.items():
        (tickets_dir / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")

    pipeline = _FakePipeline(
        {
            "low_conf": [0.3, 0.2],
            "no_terms": [0.9, 0.1],
            "pattern_empty": [0.9, 0.1],
            "two_terms": [0.9, 0.1],
            "one_term": [0.9, 0.1],
            "other_case": [0.9, 0.1],
        }
    )
    review_rows = [
        {"Ticket": "HPC-MISSING", "Project Key": "HPC"},
        {"Ticket": "HPC-EMPTY", "Project Key": "HPC"},
        {"Ticket": "HPC-LOW", "Project Key": "HPC"},
        {"Ticket": "HPC-NO-TERMS", "Project Key": "HPC"},
        {"Ticket": "HPC-PATTERN-EMPTY", "Project Key": "HPC"},
        {"Ticket": "HPC-TWO", "Project Key": "HPC"},
        {"Ticket": "HPC-ONE", "Project Key": "HPC"},
        {"Ticket": "HPC-OTHER", "Project Key": "HPC"},
    ]

    proposals = run_training.generate_ml_proposals(
        review_rows,
        pipeline,
        {"COI_A": "CategoryA"},
        tickets_dir,
    )

    assert len(proposals) == 3
    assert proposals[0]["Ticket"] == "HPC-TWO"
    assert proposals[0]["Rule Pattern"] == "cable.*i2c"
    assert proposals[1]["Ticket"] == "HPC-ONE"
    assert proposals[1]["Rule Pattern"] == "network"
    assert proposals[2]["Ticket"] == "HPC-OTHER"
    assert proposals[2]["Rule Pattern"] == "other"


def test_main_ml_engine_auto_rules_no_tickets_dir(monkeypatch, tmp_path):
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [])

    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(tickets, TICKET_HEADER, [
        {
            "Project Key": "HPC",
            "Ticket": "HPC-200",
            "Ticket Description": "review me",
            "Category of Issue": "uncategorized",
            "Category": "unknown",
            "Human Audit for Accuracy": "needs-review",
            "Human Comments": "",
        }
    ])

    model_path = tmp_path / "classifier.joblib"
    map_path = tmp_path / "category_map.json"
    model_path.write_text("model", encoding="utf-8")
    map_path.write_text("{}", encoding="utf-8")

    fake_ml_module = SimpleNamespace(
        load_model=lambda _m, _c: (object(), {"X": "Y"})
    )
    monkeypatch.setitem(sys.modules, "ml_classifier", fake_ml_module)
    monkeypatch.setattr(run_training, "find_latest_tickets_dir", lambda: None)
    monkeypatch.setattr(run_training, "generate_ml_proposals", lambda *_args, **_kwargs: [])

    result = _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--engine",
        "ml",
        "--ml-model",
        str(model_path),
        "--ml-category-map",
        str(map_path),
        "--auto-rules",
        "--output-rule-engine",
        str(tmp_path / "rule-engine.local.csv"),
    )
    assert result["rules_added"] == 0


def test_invalid_regex_proposals_are_skipped(tmp_path, monkeypatch):
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

    def fake_run_invalid_regex(cmd, input, text, capture_output, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
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
                }
            ),
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

    with pytest.raises(AssertionError, match="subprocess.run should not be called"):
        fail_if_called()

    monkeypatch.setattr(run_training.subprocess, "run", fail_if_called)
    assert run_training.call_codex("prompt", [], 10) == []


def test_main_prints_no_proposals_reason_when_all_rejected(tmp_path, monkeypatch, capsys):
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
    _write_csv(tickets, TICKET_HEADER, [{
        "Project Key": "DO",
        "Ticket": "DO-100",
        "Ticket Description": "bad row",
        "Category of Issue": "CPU",
        "Category": "CPU/Processor",
        "Human Audit for Accuracy": "incorrect",
        "Human Comments": "needs correction",
    }])

    output = tmp_path / "rule-engine.local.csv"

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
        "prompt",
        "--output-rule-engine",
        str(output),
    )
    out = capsys.readouterr().out
    assert "No proposals reason: all_proposals_rejected" in out


def test_main_prints_no_review_rows_reason_when_none_selected(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [])

    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(tickets, TICKET_HEADER, [{
        "Project Key": "DO",
        "Ticket": "DO-100",
        "Ticket Description": "already correct",
        "Category of Issue": "CPU",
        "Category": "CPU/Processor",
        "Human Audit for Accuracy": "correct",
        "Human Comments": "",
    }])

    def fail_if_called(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called when no review rows")

    with pytest.raises(AssertionError, match="subprocess.run should not be called"):
        fail_if_called()

    monkeypatch.setattr(run_training.subprocess, "run", fail_if_called)
    _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--prompt",
        "prompt",
        "--output-rule-engine",
        str(tmp_path / "rule-engine.local.csv"),
    )
    out = capsys.readouterr().out
    assert "No proposals reason: no_review_rows=1" in out


def test_main_writes_log_file(tmp_path, monkeypatch):
    monkeypatch.setattr(run_training, "REPO_ROOT", tmp_path)
    rules = tmp_path / "source-rule-engine.csv"
    _write_csv(rules, RULE_HEADER, [])
    tickets = tmp_path / "tickets-categorized.csv"
    _write_csv(tickets, TICKET_HEADER, [{
        "Project Key": "DO",
        "Ticket": "DO-100",
        "Ticket Description": "already correct",
        "Category of Issue": "CPU",
        "Category": "CPU/Processor",
        "Human Audit for Accuracy": "correct",
        "Human Comments": "",
    }])

    result = _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--prompt",
        "prompt",
        "--output-rule-engine",
        str(tmp_path / "rule-engine.local.csv"),
    )

    log_file = Path(result["log_file"])
    assert log_file.exists()
    text = log_file.read_text(encoding="utf-8")
    assert "Run started at:" in text


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
    assert observed["payload"].startswith("inline prompt text\n\nRESPONSE FORMAT (STRICT):")
    assert "INPUT JSON:" in observed["payload"]

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
    assert observed["payload"].startswith("markdown prompt text\n\nRESPONSE FORMAT (STRICT):")
    assert "INPUT JSON:" in observed["payload"]


def test_long_inline_prompt_is_not_treated_as_path():
    long_prompt = "x" * 5000
    assert run_training.load_prompt_text(long_prompt, None) == long_prompt


def test_main_prints_truncated_prompt_preview(tmp_path, monkeypatch, capsys):
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

    output = tmp_path / "rule-engine-inline.csv"

    def fake_run(cmd, input, text, capture_output, **kwargs):
        return SimpleNamespace(returncode=0, stdout='{"proposals": []}', stderr="")

    monkeypatch.setattr(run_training.subprocess, "run", fake_run)

    _run_main(
        "--tickets-categorized",
        str(tickets),
        "--rules-engine-file",
        str(rules),
        "--prompt",
        "x" * 250,
        "--output-rule-engine",
        str(output),
    )
    out = capsys.readouterr().out
    assert "Prompt preview:" in out
    assert "..." in out
