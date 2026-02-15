#!/usr/bin/env python3
"""
Local ML classifier for ticket categorization.

Provides a TF-IDF + SGDClassifier pipeline as a fallback for tickets
that the rule engine cannot match.  The module is used by:

- ``ml_train.py``  — to train and serialize a model
- ``rule_engine_categorize.py`` — to predict categories at inference time
"""

import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline

# Minimum confidence to accept an ML prediction as usable
ML_CONFIDENCE_THRESHOLD = 0.4

# Minimum number of labeled samples required to train
MIN_TRAINING_SAMPLES = 20


def build_feature_text(ticket_data):
    """Concatenate summary + description + labels + comments into one string.

    Mirrors the fields inspected by ``get_ticket_field_text`` in
    ``rule_engine_categorize.py`` so that the ML model sees the same text
    surface the rule engine does.
    """
    parts = []
    summary = ticket_data.get("ticket", {}).get("summary", "")
    if summary:
        parts.append(summary)
    description = ticket_data.get("description", "")
    if description:
        parts.append(description)
    labels = ticket_data.get("labels", [])
    if labels:
        parts.append(" ".join(labels))
    for c in ticket_data.get("comments", []):
        body = c.get("body", "")
        if body:
            parts.append(body)
    return " ".join(parts)


def build_pipeline():
    """Return an untrained sklearn Pipeline (TF-IDF + SGDClassifier)."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
            stop_words="english",
        )),
        ("clf", SGDClassifier(
            loss="modified_huber",
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )),
    ])


def train_model(texts, labels):
    """Train the pipeline on labeled data.

    Parameters
    ----------
    texts : list[str]
        Feature text for each ticket (output of ``build_feature_text``).
    labels : list[str]
        Ground-truth ``Category of Issue`` label for each ticket.

    Returns
    -------
    tuple[Pipeline, dict]
        The fitted pipeline and a metrics dict with keys
        ``"cv_accuracy"``, ``"n_samples"``, ``"n_classes"``,
        and ``"report"`` (the sklearn classification report string).

    Raises
    ------
    ValueError
        If fewer than ``MIN_TRAINING_SAMPLES`` samples are provided.
    """
    if len(texts) < MIN_TRAINING_SAMPLES:
        raise ValueError(
            f"Need at least {MIN_TRAINING_SAMPLES} samples to train, "
            f"got {len(texts)}"
        )

    pipeline = build_pipeline()

    # If min_df=2 would eliminate all features (very small datasets),
    # rebuild with min_df=1
    unique_classes = sorted(set(labels))
    if len(texts) < 50:
        pipeline.set_params(tfidf__min_df=1)

    pipeline.fit(texts, labels)

    # Cross-validation (use at most 3 folds, or fewer if classes are small)
    n_folds = min(3, min(labels.count(c) for c in unique_classes))
    if n_folds >= 2:
        cv_scores = cross_val_score(pipeline, texts, labels, cv=n_folds)
        cv_accuracy = float(cv_scores.mean())
    else:
        cv_accuracy = -1.0  # not enough data for CV

    # Refit on full data after CV
    pipeline.fit(texts, labels)

    report = classification_report(labels, pipeline.predict(texts))

    metrics = {
        "cv_accuracy": round(cv_accuracy, 4),
        "n_samples": len(texts),
        "n_classes": len(unique_classes),
        "report": report,
    }
    return pipeline, metrics


def save_model(pipeline, category_map, model_path, map_path):
    """Serialize the trained pipeline and category map to disk.

    Parameters
    ----------
    pipeline : Pipeline
        Fitted sklearn pipeline.
    category_map : dict
        Mapping from ``Category of Issue`` to ``Category``.
    model_path : Path | str
        Where to write the joblib file.
    map_path : Path | str
        Where to write the JSON category map.
    """
    model_path = Path(model_path)
    map_path = Path(map_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(category_map, f, indent=2)


def load_model(model_path, map_path):
    """Load a serialized pipeline and category map.

    Returns
    -------
    tuple[Pipeline, dict]
        The deserialized pipeline and category map.

    Raises
    ------
    FileNotFoundError
        If either file does not exist.
    """
    model_path = Path(model_path)
    map_path = Path(map_path)
    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not map_path.is_file():
        raise FileNotFoundError(f"Category map not found: {map_path}")
    pipeline = joblib.load(model_path)
    with open(map_path, encoding="utf-8") as f:
        category_map = json.load(f)
    return pipeline, category_map


def predict(pipeline, category_map, ticket_data):
    """Predict category for a single ticket.

    Parameters
    ----------
    pipeline : Pipeline
        Fitted sklearn pipeline.
    category_map : dict
        ``Category of Issue`` → ``Category`` mapping.
    ticket_data : dict
        Normalized ticket JSON.

    Returns
    -------
    tuple[str, str, float]
        ``(category_of_issue, category, confidence)``
    """
    text = build_feature_text(ticket_data)
    if not text.strip():
        return "uncategorized", "unknown", 0.0

    proba = pipeline.predict_proba([text])[0]
    classes = pipeline.classes_
    best_idx = proba.argmax()
    category_of_issue = classes[best_idx]
    confidence = float(proba[best_idx])
    category = category_map.get(category_of_issue, "unknown")
    return category_of_issue, category, round(confidence, 4)


if __name__ == "__main__":
    print("This module is not meant to be run directly. "
          "Use ml_train.py to train or rule_engine_categorize.py to predict.")
