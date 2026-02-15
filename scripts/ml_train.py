#!/usr/bin/env python3
"""Train a local ML classifier for ticket categorization.

Assembles training data from:
1. A human-labeled CSV (``--training-data``)
2. Auto-harvested rule-matched tickets from ``tickets-categorized.csv``

Outputs a serialized sklearn pipeline and category map that can be
used by ``rule_engine_categorize.py --ml-model``.

Usage:
    python3 scripts/ml_train.py \\
        --training-data scripts/trained-data/ml-training-data.csv \\
        --tickets-dir scripts/normalized-tickets/2026-02-08

    python3 scripts/ml_train.py \\
        --training-data scripts/trained-data/ml-training-data.csv \\
        --tickets-categorized scripts/analysis/tickets-categorized.csv \\
        --tickets-dir scripts/normalized-tickets/2026-02-08
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_MODEL = (
    REPO_ROOT / "scripts" / "trained-data" / "ml-model" / "classifier.joblib"
)
DEFAULT_OUTPUT_MAP = (
    REPO_ROOT / "scripts" / "trained-data" / "ml-model" / "category_map.json"
)
DEFAULT_REPORT = (
    REPO_ROOT / "scripts" / "trained-data" / "ml-model" / "training_report.txt"
)

TRAINING_DATA_COLUMNS = {
    "Ticket", "Category of Issue", "Category",
}

CATEGORIZED_COLUMNS = {
    "Ticket", "Category of Issue", "Category",
    "Categorization Source", "Human Audit for Accuracy",
}


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Train a local ML classifier for ticket categorization")
    p.add_argument(
        "--training-data", type=Path, required=True,
        help="CSV with human-labeled tickets "
             "(columns: Ticket, Category of Issue, Category)")
    p.add_argument(
        "--tickets-categorized", type=Path, default=None,
        help="tickets-categorized.csv to auto-harvest labels from "
             "rule-matched, human-audited tickets")
    p.add_argument(
        "--tickets-dir", type=Path, default=None,
        help="Directory with normalized ticket JSONs. Used to build "
             "feature text for each ticket. If not given, falls back "
             "to the most recent date folder.")
    p.add_argument(
        "--output-model", type=Path, default=DEFAULT_OUTPUT_MODEL,
        help="Where to save the trained model (.joblib)")
    p.add_argument(
        "--output-category-map", type=Path, default=DEFAULT_OUTPUT_MAP,
        help="Where to save category_map.json")
    p.add_argument(
        "--output-report", type=Path, default=DEFAULT_REPORT,
        help="Where to save the training report")
    p.add_argument(
        "--min-samples", type=int, default=20,
        help="Minimum labeled samples required to train (default: 20)")
    p.add_argument(
        "-y", "--yes", action="store_true",
        help="Skip confirmation prompts")
    return p.parse_args(argv)


def load_training_csv(path):
    """Load human-labeled training data CSV.

    Returns list of dicts with keys: Ticket, Category of Issue, Category.
    Rows with empty Category of Issue are skipped.
    """
    if not path.is_file():
        sys.exit(f"Training data file not found: {path}")

    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            sys.exit(f"Training data CSV is empty: {path}")
        missing = TRAINING_DATA_COLUMNS - set(reader.fieldnames)
        if missing:
            sys.exit(
                f"Training data CSV missing columns: {sorted(missing)}")
        for row in reader:
            if not row.get("Category of Issue", "").strip():
                continue
            rows.append({
                "Ticket": row["Ticket"].strip(),
                "Category of Issue": row["Category of Issue"].strip(),
                "Category": row.get("Category", "").strip(),
            })
    return rows


def harvest_labels(path):
    """Auto-harvest labels from tickets-categorized.csv.

    Includes rows where:
    - Categorization Source == "rule" AND
    - Human Audit for Accuracy in ("correct", "pending-review")

    Returns list of dicts with keys: Ticket, Category of Issue, Category.
    """
    if not path or not path.is_file():
        return []

    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return []
        missing = CATEGORIZED_COLUMNS - set(reader.fieldnames)
        if missing:
            return []
        for row in reader:
            source = row.get("Categorization Source", "").strip()
            audit = row.get("Human Audit for Accuracy", "").strip()
            cat_of_issue = row.get("Category of Issue", "").strip()
            if (source == "rule"
                    and audit in ("correct", "pending-review")
                    and cat_of_issue
                    and cat_of_issue != "uncategorized"):
                rows.append({
                    "Ticket": row["Ticket"].strip(),
                    "Category of Issue": cat_of_issue,
                    "Category": row.get("Category", "").strip(),
                })
    return rows


def find_latest_tickets_dir():
    """Pick the most recent date folder under scripts/normalized-tickets/."""
    base = REPO_ROOT / "scripts" / "normalized-tickets"
    if not base.is_dir():
        return None
    date_dirs = sorted(d for d in base.iterdir() if d.is_dir())
    return date_dirs[-1] if date_dirs else None


def load_ticket_texts(tickets_dir, ticket_keys):
    """Load normalized ticket JSONs and build feature text for each.

    Returns dict mapping ticket key → feature text string.
    """
    # Import here to avoid circular dependency at module level
    from ml_classifier import build_feature_text

    if not tickets_dir or not tickets_dir.is_dir():
        return {}

    texts = {}
    for json_file in tickets_dir.glob("*.json"):
        ticket_key = json_file.stem
        if ticket_key not in ticket_keys:
            continue
        with open(json_file, encoding="utf-8") as f:
            ticket_data = json.load(f)
        texts[ticket_key] = build_feature_text(ticket_data)
    return texts


def build_category_map(labeled_rows):
    """Build Category of Issue → Category mapping from labeled data."""
    cat_map = {}
    for row in labeled_rows:
        coi = row["Category of Issue"]
        cat = row.get("Category", "")
        if coi and cat:
            cat_map[coi] = cat
    return cat_map


def main(argv=None):
    args = parse_args(argv)

    # Import here so tests can mock
    from ml_classifier import save_model, train_model, ML_CONFIDENCE_THRESHOLD

    # --- Load labeled data ---
    print(f"Loading training data from: {args.training_data}")
    human_labels = load_training_csv(args.training_data)
    print(f"  Human-labeled samples: {len(human_labels)}")

    harvested = harvest_labels(args.tickets_categorized)
    if harvested:
        print(f"  Auto-harvested samples: {len(harvested)}")

    # Merge, dedup by ticket key (human labels take precedence)
    seen = set()
    all_labels = []
    for row in human_labels:
        if row["Ticket"] not in seen:
            seen.add(row["Ticket"])
            all_labels.append(row)
    for row in harvested:
        if row["Ticket"] not in seen:
            seen.add(row["Ticket"])
            all_labels.append(row)

    print(f"  Total unique labeled samples: {len(all_labels)}")

    if len(all_labels) < args.min_samples:
        sys.exit(
            f"Not enough labeled data: {len(all_labels)} samples "
            f"(need at least {args.min_samples}). "
            "Label more tickets in the training data CSV."
        )

    # --- Load ticket texts ---
    tickets_dir = args.tickets_dir or find_latest_tickets_dir()
    ticket_keys = {row["Ticket"] for row in all_labels}
    ticket_texts = load_ticket_texts(tickets_dir, ticket_keys)

    if tickets_dir:
        print(f"  Ticket JSONs loaded: {len(ticket_texts)} "
              f"(from {tickets_dir})")

    # Build feature texts — fall back to Category of Issue as text if
    # the normalized JSON is not available
    texts = []
    labels = []
    for row in all_labels:
        text = ticket_texts.get(row["Ticket"], "")
        if not text:
            # Minimal fallback: use the label itself as text
            # (not ideal but allows training without all JSONs)
            text = row["Category of Issue"]
        texts.append(text)
        labels.append(row["Category of Issue"])

    # Warn about underrepresented classes
    from collections import Counter
    class_counts = Counter(labels)
    for cls, count in sorted(class_counts.items()):
        if count < 3:
            print(f"  WARNING: class '{cls}' has only {count} sample(s)")

    # --- Train ---
    print(f"\nTraining model on {len(texts)} samples "
          f"across {len(class_counts)} classes...")
    pipeline, metrics = train_model(texts, labels)

    print(f"  Cross-validation accuracy: {metrics['cv_accuracy']}")
    print(f"\n{metrics['report']}")

    # --- Build category map ---
    category_map = build_category_map(all_labels)

    # --- Save ---
    save_model(pipeline, category_map, args.output_model,
               args.output_category_map)
    print(f"\nModel saved to: {args.output_model}")
    print(f"Category map saved to: {args.output_category_map}")

    # Write training report
    report_path = args.output_report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_content = (
        f"Training Report\n"
        f"===============\n"
        f"Timestamp: {timestamp}\n"
        f"Training samples: {metrics['n_samples']}\n"
        f"Classes: {metrics['n_classes']}\n"
        f"CV Accuracy: {metrics['cv_accuracy']}\n"
        f"Confidence threshold: {ML_CONFIDENCE_THRESHOLD}\n"
        f"\nClass distribution:\n"
    )
    for cls, count in sorted(class_counts.items()):
        report_content += f"  {cls}: {count}\n"
    report_content += f"\nClassification Report:\n{metrics['report']}\n"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
