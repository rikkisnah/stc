"""#ai-assisted tests for get_tickets CLI env validation and usage."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "get_tickets.py"


def run_cli(env=None, args=None):
    cmd = [sys.executable, str(SCRIPT_PATH)]
    if args:
        cmd += args
    result = subprocess.run(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result


def test_missing_env_json_shows_warning(tmp_path, monkeypatch):
    env = os.environ.copy()
    env.pop("JIRA_TOKEN", None)
    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).resolve().parents[1] / "scripts"))
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "scripts")
    env["CONFIG_ENV_PATH"] = str(tmp_path / "env.json")
    result = run_cli(env=env, args=["-a"])
    assert "Warning" in result.stdout


def test_usage_help_when_no_action(monkeypatch):
    result = run_cli(args=[])
    assert "usage" in result.stdout.lower()
