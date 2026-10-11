"""Optional local checks against frozen private data, skipped on public CI."""

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer

from pipeline import ROOT, normalized, safe_text
from serving import predict

PRIVATE = ROOT / "data/private/clean.parquet"
pytestmark = pytest.mark.skipif(not PRIVATE.exists(), reason="Frozen narratives remain private")


def test_training_only_vocabulary_idf_and_split_leakage():
    frame = pd.read_parquet(PRIVATE)
    vectorizer, model, _ = joblib.load(ROOT / "data/private/model.joblib")
    train = frame[frame["split"] == "train"]
    rebuilt = TfidfVectorizer(preprocessor=safe_text, min_df=3, sublinear_tf=True)
    rebuilt.fit(train["text"])
    assert rebuilt.vocabulary_ == vectorizer.vocabulary_
    np.testing.assert_allclose(rebuilt.idf_, vectorizer.idf_, atol=1e-12)
    assert set(model.classes_) == set(train["product"])
    assert not frame["text"].map(normalized).duplicated().any()
    periods = [
        frame.loc[frame["split"] == split, "date"]
        for split in ["train", "tune", "calibration", "test"]
    ]
    assert all(a.max() < b.min() for a, b in zip(periods, periods[1:], strict=False))


def test_exported_inference_matches_sklearn_on_real_test_records():
    vectorizer, model, _ = joblib.load(ROOT / "data/private/model.joblib")
    frame = pd.read_parquet(PRIVATE)
    test = frame[frame["split"] == "test"].head(30)
    expected = model.predict_proba(vectorizer.transform(test["text"]))
    actual = np.array([predict(text)["probabilities"] for text in test["text"]])
    np.testing.assert_allclose(actual, expected, atol=1e-10)
