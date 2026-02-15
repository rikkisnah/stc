"""Tests for ml_train.py"""

import csv
import json
from pathlib import Path
from unittest.mock import patch

import pytest

import ml_train


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TRAINING_HEADER = ["Ticket", "Category of Issue", "Category",
                   "Label Source", "Label Date", "Notes"]

CATEGORIZED_HEADER = [
    "Project Key", "Ticket", "Ticket URL", "Ticket Description",
    "Status", "Created", "Age", "Runbook Present",
    "Category of Issue", "Category", "Rules Used",
    "Categorization Source", "LLM Confidence",
    "Human Audit for Accuracy", "Human Audit Guidance", "Human Comments",
]


def _write_training_csv(path, rows, header=None):
    """Write a training data CSV."""
    header = header or TRAINING_HEADER
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_categorized_csv(path, rows):
    """Write a tickets-categorized CSV."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CATEGORIZED_HEADER)
        writer.writeheader()
        for row in rows:
            # Fill in defaults for missing fields
            full_row = {h: "" for h in CATEGORIZED_HEADER}
            full_row.update(row)
            writer.writerow(full_row)


def _write_ticket_json(directory, ticket_key, summary="test",
                       description="test desc"):
    """Write a minimal normalized ticket JSON."""
    data = {
        "ticket": {"key": ticket_key, "summary": summary,
                   "project": {"key": "DO"}},
        "description": description,
        "labels": [],
        "comments": [],
        "status": {"current": "Open", "created": "2026-01-01T00:00:00Z"},
    }
    path = directory / f"{ticket_key}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def _make_training_rows(n_per_class=10):
    """Build training CSV rows with 3 classes."""
    rows = []
    classes = {
        "GPU Failure": "GPU",
        "Network Issue": "NET",
        "Storage Problem": "STORAGE",
    }
    i = 0
    for cat_of_issue, category in classes.items():
        for j in range(n_per_class):
            rows.append({
                "Ticket": f"DO-{i:07d}",
                "Category of Issue": cat_of_issue,
                "Category": category,
                "Label Source": "human",
                "Label Date": "2026-02-15",
                "Notes": "",
            })
            i += 1
    return rows


def _setup_training_env(tmp_path, n_per_class=10, write_tickets=True,
                        categorized_rows=None):
    """Create training data, ticket JSONs, and return standard args."""
    training_csv = tmp_path / "training.csv"
    rows = _make_training_rows(n_per_class)
    _write_training_csv(training_csv, rows)

    tickets_dir = tmp_path / "tickets"
    tickets_dir.mkdir()
    if write_tickets:
        class_words = {
            "GPU Failure": ("gpu hardware fault", "graphics card memory error"),
            "Network Issue": ("network connectivity", "switch router cable"),
            "Storage Problem": ("storage disk drive", "raid filesystem mount"),
        }
        i = 0
        for cat, (summary, desc) in class_words.items():
            for j in range(n_per_class):
                _write_ticket_json(
                    tickets_dir, f"DO-{i:07d}",
                    summary=f"{summary} ticket {j}",
                    description=f"{desc} details {j}")
                i += 1

    output_model = tmp_path / "model" / "classifier.joblib"
    output_map = tmp_path / "model" / "category_map.json"
    output_report = tmp_path / "model" / "report.txt"

    argv = [
        "--training-data", str(training_csv),
        "--tickets-dir", str(tickets_dir),
        "--output-model", str(output_model),
        "--output-category-map", str(output_map),
        "--output-report", str(output_report),
    ]

    if categorized_rows is not None:
        cat_csv = tmp_path / "categorized.csv"
        _write_categorized_csv(cat_csv, categorized_rows)
        argv.extend(["--tickets-categorized", str(cat_csv)])

    return argv, output_model, output_map, output_report


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------

class TestParseArgs:
    def test_requires_training_data(self):
        with pytest.raises(SystemExit):
            ml_train.parse_args([])

    def test_minimal_args(self, tmp_path):
        args = ml_train.parse_args([
            "--training-data", str(tmp_path / "t.csv")])
        assert args.training_data == tmp_path / "t.csv"
        assert args.tickets_categorized is None
        assert args.min_samples == 20
        assert args.yes is False

    def test_all_args(self, tmp_path):
        args = ml_train.parse_args([
            "--training-data", str(tmp_path / "t.csv"),
            "--tickets-categorized", str(tmp_path / "c.csv"),
            "--tickets-dir", str(tmp_path / "tickets"),
            "--output-model", str(tmp_path / "m.joblib"),
            "--output-category-map", str(tmp_path / "map.json"),
            "--output-report", str(tmp_path / "report.txt"),
            "--min-samples", "10",
            "-y",
        ])
        assert args.tickets_categorized == tmp_path / "c.csv"
        assert args.min_samples == 10
        assert args.yes is True


# ---------------------------------------------------------------------------
# load_training_csv
# ---------------------------------------------------------------------------

class TestLoadTrainingCsv:
    def test_loads_valid_csv(self, tmp_path):
        path = tmp_path / "train.csv"
        _write_training_csv(path, [
            {"Ticket": "DO-001", "Category of Issue": "GPU Failure",
             "Category": "GPU", "Label Source": "human",
             "Label Date": "2026-02-15", "Notes": ""},
        ])
        rows = ml_train.load_training_csv(path)
        assert len(rows) == 1
        assert rows[0]["Ticket"] == "DO-001"
        assert rows[0]["Category of Issue"] == "GPU Failure"

    def test_skips_empty_category(self, tmp_path):
        path = tmp_path / "train.csv"
        _write_training_csv(path, [
            {"Ticket": "DO-001", "Category of Issue": "",
             "Category": "GPU", "Label Source": "", "Label Date": "",
             "Notes": ""},
            {"Ticket": "DO-002", "Category of Issue": "GPU",
             "Category": "GPU", "Label Source": "", "Label Date": "",
             "Notes": ""},
        ])
        rows = ml_train.load_training_csv(path)
        assert len(rows) == 1
        assert rows[0]["Ticket"] == "DO-002"

    def test_file_not_found_exits(self, tmp_path):
        with pytest.raises(SystemExit, match="not found"):
            ml_train.load_training_csv(tmp_path / "nonexistent.csv")

    def test_missing_columns_exits(self, tmp_path):
        path = tmp_path / "bad.csv"
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Ticket", "Notes"])
            writer.writeheader()
        with pytest.raises(SystemExit, match="missing columns"):
            ml_train.load_training_csv(path)

    def test_empty_csv_exits(self, tmp_path):
        path = tmp_path / "empty.csv"
        path.write_text("")
        with pytest.raises(SystemExit, match="empty"):
            ml_train.load_training_csv(path)


# ---------------------------------------------------------------------------
# harvest_labels
# ---------------------------------------------------------------------------

class TestHarvestLabels:
    def test_harvests_rule_correct_rows(self, tmp_path):
        path = tmp_path / "cat.csv"
        _write_categorized_csv(path, [
            {"Ticket": "DO-001", "Category of Issue": "GPU Failure",
             "Category": "GPU", "Categorization Source": "rule",
             "Human Audit for Accuracy": "correct"},
        ])
        rows = ml_train.harvest_labels(path)
        assert len(rows) == 1
        assert rows[0]["Ticket"] == "DO-001"

    def test_harvests_pending_review(self, tmp_path):
        path = tmp_path / "cat.csv"
        _write_categorized_csv(path, [
            {"Ticket": "DO-002", "Category of Issue": "Net Issue",
             "Category": "NET", "Categorization Source": "rule",
             "Human Audit for Accuracy": "pending-review"},
        ])
        rows = ml_train.harvest_labels(path)
        assert len(rows) == 1

    def test_skips_incorrect(self, tmp_path):
        path = tmp_path / "cat.csv"
        _write_categorized_csv(path, [
            {"Ticket": "DO-003", "Category of Issue": "Bad",
             "Category": "X", "Categorization Source": "rule",
             "Human Audit for Accuracy": "incorrect"},
        ])
        rows = ml_train.harvest_labels(path)
        assert len(rows) == 0

    def test_skips_non_rule_source(self, tmp_path):
        path = tmp_path / "cat.csv"
        _write_categorized_csv(path, [
            {"Ticket": "DO-004", "Category of Issue": "GPU",
             "Category": "GPU", "Categorization Source": "none",
             "Human Audit for Accuracy": "correct"},
        ])
        rows = ml_train.harvest_labels(path)
        assert len(rows) == 0

    def test_skips_uncategorized(self, tmp_path):
        path = tmp_path / "cat.csv"
        _write_categorized_csv(path, [
            {"Ticket": "DO-005", "Category of Issue": "uncategorized",
             "Category": "unknown", "Categorization Source": "rule",
             "Human Audit for Accuracy": "correct"},
        ])
        rows = ml_train.harvest_labels(path)
        assert len(rows) == 0

    def test_none_path_returns_empty(self):
        assert ml_train.harvest_labels(None) == []

    def test_missing_file_returns_empty(self, tmp_path):
        assert ml_train.harvest_labels(tmp_path / "nope.csv") == []

    def test_missing_columns_returns_empty(self, tmp_path):
        path = tmp_path / "bad.csv"
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Ticket", "Notes"])
            writer.writeheader()
        assert ml_train.harvest_labels(path) == []

    def test_empty_csv_returns_empty(self, tmp_path):
        path = tmp_path / "empty.csv"
        path.write_text("")
        assert ml_train.harvest_labels(path) == []


# ---------------------------------------------------------------------------
# find_latest_tickets_dir
# ---------------------------------------------------------------------------

class TestFindLatestTicketsDir:
    def test_returns_latest(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ml_train, "REPO_ROOT", tmp_path)
        base = tmp_path / "scripts" / "normalized-tickets"
        (base / "2026-01-01").mkdir(parents=True)
        (base / "2026-02-15").mkdir(parents=True)
        result = ml_train.find_latest_tickets_dir()
        assert result == base / "2026-02-15"

    def test_no_base_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ml_train, "REPO_ROOT", tmp_path)
        assert ml_train.find_latest_tickets_dir() is None

    def test_empty_base_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ml_train, "REPO_ROOT", tmp_path)
        (tmp_path / "scripts" / "normalized-tickets").mkdir(parents=True)
        assert ml_train.find_latest_tickets_dir() is None


# ---------------------------------------------------------------------------
# load_ticket_texts
# ---------------------------------------------------------------------------

class TestLoadTicketTexts:
    def test_loads_matching_tickets(self, tmp_path):
        _write_ticket_json(tmp_path, "DO-001", summary="gpu error")
        _write_ticket_json(tmp_path, "DO-002", summary="net issue")
        texts = ml_train.load_ticket_texts(tmp_path, {"DO-001"})
        assert "DO-001" in texts
        assert "gpu error" in texts["DO-001"]
        assert "DO-002" not in texts

    def test_none_dir_returns_empty(self):
        assert ml_train.load_ticket_texts(None, {"DO-001"}) == {}

    def test_missing_dir_returns_empty(self, tmp_path):
        assert ml_train.load_ticket_texts(
            tmp_path / "nope", {"DO-001"}) == {}


# ---------------------------------------------------------------------------
# build_category_map
# ---------------------------------------------------------------------------

class TestBuildCategoryMap:
    def test_builds_map(self):
        rows = [
            {"Category of Issue": "GPU Failure", "Category": "GPU"},
            {"Category of Issue": "Net Issue", "Category": "NET"},
        ]
        cat_map = ml_train.build_category_map(rows)
        assert cat_map == {"GPU Failure": "GPU", "Net Issue": "NET"}

    def test_skips_empty_category(self):
        rows = [
            {"Category of Issue": "GPU Failure", "Category": ""},
        ]
        cat_map = ml_train.build_category_map(rows)
        assert cat_map == {}

    def test_empty_input(self):
        assert ml_train.build_category_map([]) == {}


# ---------------------------------------------------------------------------
# main (integration)
# ---------------------------------------------------------------------------

class TestMain:
    def test_end_to_end(self, tmp_path, capsys):
        argv, model_path, map_path, report_path = _setup_training_env(
            tmp_path, n_per_class=10)
        ml_train.main(argv)

        assert model_path.is_file()
        assert map_path.is_file()
        assert report_path.is_file()

        with open(map_path) as f:
            cat_map = json.load(f)
        assert "GPU Failure" in cat_map
        assert cat_map["GPU Failure"] == "GPU"

        output = capsys.readouterr().out
        assert "Training model on" in output
        assert "Model saved to" in output

    def test_insufficient_data_exits(self, tmp_path):
        training_csv = tmp_path / "training.csv"
        _write_training_csv(training_csv, [
            {"Ticket": "DO-001", "Category of Issue": "GPU",
             "Category": "GPU", "Label Source": "", "Label Date": "",
             "Notes": ""},
        ])
        argv = ["--training-data", str(training_csv),
                "--min-samples", "20"]
        with pytest.raises(SystemExit, match="Not enough"):
            ml_train.main(argv)

    def test_with_harvested_labels(self, tmp_path, capsys):
        cat_rows = []
        for i in range(10):
            cat_rows.append({
                "Ticket": f"DO-H{i:05d}",
                "Category of Issue": "Harvested Cat",
                "Category": "HARV",
                "Categorization Source": "rule",
                "Human Audit for Accuracy": "correct",
            })

        argv, model_path, map_path, report_path = _setup_training_env(
            tmp_path, n_per_class=7, categorized_rows=cat_rows)
        ml_train.main(argv)

        output = capsys.readouterr().out
        assert "Auto-harvested samples: 10" in output
        assert model_path.is_file()

    def test_dedup_human_takes_precedence(self, tmp_path, capsys):
        """If a ticket appears in both human labels and harvested,
        human label wins."""
        cat_rows = [{
            "Ticket": "DO-0000000",  # same as first training row
            "Category of Issue": "WRONG",
            "Category": "WRONG",
            "Categorization Source": "rule",
            "Human Audit for Accuracy": "correct",
        }]
        argv, model_path, _, _ = _setup_training_env(
            tmp_path, n_per_class=10, categorized_rows=cat_rows)
        ml_train.main(argv)

        output = capsys.readouterr().out
        # Total should be 30 (not 31), because the harvested duplicate
        # was deduped away
        assert "Total unique labeled samples: 30" in output

    def test_without_ticket_jsons(self, tmp_path, capsys):
        """Training still works using fallback text when no JSONs exist."""
        argv, model_path, _, _ = _setup_training_env(
            tmp_path, n_per_class=10, write_tickets=False)
        ml_train.main(argv)
        assert model_path.is_file()
        output = capsys.readouterr().out
        assert "Ticket JSONs loaded: 0" in output

    def test_report_content(self, tmp_path):
        argv, _, _, report_path = _setup_training_env(tmp_path, n_per_class=10)
        ml_train.main(argv)
        content = report_path.read_text()
        assert "Training Report" in content
        assert "Training samples:" in content
        assert "Classes:" in content
        assert "Classification Report:" in content

    def test_warns_underrepresented_classes(self, tmp_path, capsys):
        """Classes with fewer than 3 samples emit a warning."""
        training_csv = tmp_path / "training.csv"
        rows = _make_training_rows(n_per_class=10)
        # Add a single sample of a rare class
        rows.append({
            "Ticket": "DO-9999999",
            "Category of Issue": "Rare Issue",
            "Category": "RARE",
            "Label Source": "human",
            "Label Date": "2026-02-15",
            "Notes": "",
        })
        _write_training_csv(training_csv, rows)

        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()
        # Write JSONs for the 30 standard tickets
        class_words = {
            "GPU Failure": ("gpu hardware fault", "graphics memory"),
            "Network Issue": ("network switch", "cable router"),
            "Storage Problem": ("storage disk", "raid mount"),
        }
        i = 0
        for cat, (s, d) in class_words.items():
            for j in range(10):
                _write_ticket_json(tickets_dir, f"DO-{i:07d}",
                                   summary=f"{s} {j}", description=d)
                i += 1

        argv = [
            "--training-data", str(training_csv),
            "--tickets-dir", str(tickets_dir),
            "--output-model", str(tmp_path / "m.joblib"),
            "--output-category-map", str(tmp_path / "map.json"),
            "--output-report", str(tmp_path / "report.txt"),
        ]
        ml_train.main(argv)
        output = capsys.readouterr().out
        assert "WARNING: class 'Rare Issue' has only 1 sample" in output
