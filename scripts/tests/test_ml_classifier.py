"""Tests for ml_classifier.py"""

import json
from pathlib import Path

import pytest

import ml_classifier as mc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ticket(summary="test summary", description="test description",
                 labels=None, comments=None):
    """Build a minimal normalized ticket dict."""
    return {
        "ticket": {"key": "DO-1234567", "summary": summary,
                   "project": {"key": "DO"}},
        "description": description,
        "labels": labels or [],
        "comments": comments or [],
        "status": {"current": "Open", "created": "2026-01-01T00:00:00Z"},
    }


def _make_training_data(n_per_class=10):
    """Build synthetic training texts and labels with 3 classes."""
    texts = []
    labels = []
    class_words = {
        "GPU Failure": "gpu hardware fault graphics card memory error",
        "Network Issue": "network connectivity switch router cable link down",
        "Storage Problem": "storage disk drive raid filesystem mount failure",
    }
    for label, base_text in class_words.items():
        for i in range(n_per_class):
            texts.append(f"{base_text} ticket number {i} for {label}")
            labels.append(label)
    return texts, labels


# ---------------------------------------------------------------------------
# build_feature_text
# ---------------------------------------------------------------------------

class TestBuildFeatureText:
    def test_combines_summary_description_labels_comments(self):
        ticket = _make_ticket(
            summary="my summary",
            description="my description",
            labels=["LABEL_A", "LABEL_B"],
            comments=[{"body": "comment one"}, {"body": "comment two"}],
        )
        text = mc.build_feature_text(ticket)
        assert "my summary" in text
        assert "my description" in text
        assert "LABEL_A" in text
        assert "LABEL_B" in text
        assert "comment one" in text
        assert "comment two" in text

    def test_empty_ticket_returns_empty_string(self):
        text = mc.build_feature_text({})
        assert text == ""

    def test_missing_fields_gracefully_handled(self):
        ticket = {"ticket": {}}
        text = mc.build_feature_text(ticket)
        assert text == ""

    def test_empty_comment_bodies_skipped(self):
        ticket = _make_ticket(
            summary="summary",
            description="",
            comments=[{"body": ""}, {"body": "real comment"}],
        )
        text = mc.build_feature_text(ticket)
        assert "summary" in text
        assert "real comment" in text

    def test_summary_only(self):
        ticket = _make_ticket(summary="just summary", description="")
        text = mc.build_feature_text(ticket)
        assert text == "just summary"


# ---------------------------------------------------------------------------
# build_pipeline
# ---------------------------------------------------------------------------

class TestBuildPipeline:
    def test_returns_pipeline(self):
        pipeline = mc.build_pipeline()
        assert isinstance(pipeline, mc.Pipeline)

    def test_has_tfidf_and_classifier(self):
        pipeline = mc.build_pipeline()
        step_names = [name for name, _ in pipeline.steps]
        assert "tfidf" in step_names
        assert "clf" in step_names


# ---------------------------------------------------------------------------
# train_model
# ---------------------------------------------------------------------------

class TestTrainModel:
    def test_trains_on_valid_data(self):
        texts, labels = _make_training_data(n_per_class=10)
        pipeline, metrics = mc.train_model(texts, labels)
        assert pipeline is not None
        assert metrics["n_samples"] == 30
        assert metrics["n_classes"] == 3
        assert isinstance(metrics["report"], str)

    def test_cv_accuracy_populated(self):
        texts, labels = _make_training_data(n_per_class=10)
        _, metrics = mc.train_model(texts, labels)
        assert metrics["cv_accuracy"] >= 0.0

    def test_raises_on_insufficient_data(self):
        texts = ["sample"] * 5
        labels = ["cat"] * 5
        with pytest.raises(ValueError, match="Need at least"):
            mc.train_model(texts, labels)

    def test_small_dataset_uses_min_df_1(self):
        texts, labels = _make_training_data(n_per_class=7)
        assert len(texts) == 21  # just above MIN_TRAINING_SAMPLES
        pipeline, metrics = mc.train_model(texts, labels)
        assert pipeline is not None
        # Verify min_df was adjusted
        assert pipeline.named_steps["tfidf"].min_df == 1

    def test_cv_skipped_when_too_few_per_class(self):
        # 20 samples: 19 of class A, 1 of class B → can't do 2-fold CV on B
        texts = ["gpu fault error"] * 19 + ["network issue"]
        labels = ["GPU"] * 19 + ["Network"]
        pipeline, metrics = mc.train_model(texts, labels)
        assert metrics["cv_accuracy"] == -1.0


# ---------------------------------------------------------------------------
# save_model / load_model
# ---------------------------------------------------------------------------

class TestSaveAndLoadModel:
    def test_roundtrip_save_load(self, tmp_path):
        texts, labels = _make_training_data(n_per_class=10)
        pipeline, _ = mc.train_model(texts, labels)
        category_map = {"GPU Failure": "GPU", "Network Issue": "NET",
                        "Storage Problem": "STORAGE"}
        model_path = tmp_path / "model" / "classifier.joblib"
        map_path = tmp_path / "model" / "category_map.json"

        mc.save_model(pipeline, category_map, model_path, map_path)
        assert model_path.is_file()
        assert map_path.is_file()

        loaded_pipeline, loaded_map = mc.load_model(model_path, map_path)
        assert loaded_map == category_map
        # Verify loaded model can predict
        proba = loaded_pipeline.predict_proba(["gpu memory error"])
        assert proba.shape[1] == 3

    def test_load_missing_model_raises(self, tmp_path):
        map_path = tmp_path / "category_map.json"
        map_path.write_text("{}")
        with pytest.raises(FileNotFoundError, match="Model file"):
            mc.load_model(tmp_path / "nonexistent.joblib", map_path)

    def test_load_missing_map_raises(self, tmp_path):
        # Create a valid model file first
        texts, labels = _make_training_data(n_per_class=10)
        pipeline, _ = mc.train_model(texts, labels)
        model_path = tmp_path / "classifier.joblib"
        mc.save_model(pipeline, {}, model_path, tmp_path / "real_map.json")

        with pytest.raises(FileNotFoundError, match="Category map"):
            mc.load_model(model_path, tmp_path / "nonexistent.json")

    def test_category_map_json_content(self, tmp_path):
        map_path = tmp_path / "category_map.json"
        mc.save_model(mc.build_pipeline(), {"A": "B"}, tmp_path / "m.joblib", map_path)
        with open(map_path) as f:
            data = json.load(f)
        assert data == {"A": "B"}

    def test_creates_parent_dirs(self, tmp_path):
        model_path = tmp_path / "a" / "b" / "model.joblib"
        map_path = tmp_path / "c" / "d" / "map.json"
        mc.save_model(mc.build_pipeline(), {}, model_path, map_path)
        assert model_path.is_file()
        assert map_path.is_file()


# ---------------------------------------------------------------------------
# predict
# ---------------------------------------------------------------------------

class TestPredict:
    @pytest.fixture()
    def trained_model(self):
        texts, labels = _make_training_data(n_per_class=10)
        pipeline, _ = mc.train_model(texts, labels)
        category_map = {"GPU Failure": "GPU", "Network Issue": "NET",
                        "Storage Problem": "STORAGE"}
        return pipeline, category_map

    def test_returns_category_and_confidence(self, trained_model):
        pipeline, category_map = trained_model
        ticket = _make_ticket(summary="gpu hardware fault memory error")
        cat_of_issue, category, confidence = mc.predict(
            pipeline, category_map, ticket)
        assert cat_of_issue in ("GPU Failure", "Network Issue", "Storage Problem")
        assert isinstance(confidence, float)

    def test_confidence_between_0_and_1(self, trained_model):
        pipeline, category_map = trained_model
        ticket = _make_ticket(summary="gpu card error")
        _, _, confidence = mc.predict(pipeline, category_map, ticket)
        assert 0.0 <= confidence <= 1.0

    def test_empty_text_returns_uncategorized(self, trained_model):
        pipeline, category_map = trained_model
        ticket = _make_ticket(summary="", description="")
        cat_of_issue, category, confidence = mc.predict(
            pipeline, category_map, ticket)
        assert cat_of_issue == "uncategorized"
        assert category == "unknown"
        assert confidence == 0.0

    def test_unknown_category_maps_to_unknown(self, trained_model):
        pipeline, _ = trained_model
        # Category map that doesn't contain the predicted class
        sparse_map = {}
        ticket = _make_ticket(summary="gpu fault hardware memory error")
        _, category, _ = mc.predict(pipeline, sparse_map, ticket)
        assert category == "unknown"

    def test_predict_gpu_ticket(self, trained_model):
        pipeline, category_map = trained_model
        ticket = _make_ticket(
            summary="gpu hardware fault graphics card memory error")
        cat_of_issue, category, confidence = mc.predict(
            pipeline, category_map, ticket)
        assert cat_of_issue == "GPU Failure"
        assert category == "GPU"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_threshold_value(self):
        assert mc.ML_CONFIDENCE_THRESHOLD == 0.4

    def test_min_training_samples(self):
        assert mc.MIN_TRAINING_SAMPLES == 20
