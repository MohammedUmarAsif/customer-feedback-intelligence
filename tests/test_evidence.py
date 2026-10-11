"""Public evidence integrity checks, plus explicitly synthetic edge fixtures."""

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from insights import priority_guidance
from pipeline import SAFE, choose_threshold, deduplicate, map_labels, safe_text, split_for, wilson
from serving import EXAMPLES, MODEL, app, predict

ROOT = Path(__file__).parents[1]
DATA = json.loads((ROOT / "site/data.json").read_text())


def test_priority_guidance_survives_ranking_changes():
    for row in reversed(DATA["insights"]["priorities"]):
        assert priority_guidance(row["product"], row["issue"]) == (
            row["recommendation"],
            row["next_check"],
        )
    unknown = priority_guidance("Mortgage", "A newly dominant issue")
    assert "debt-ownership" not in unknown[0]
    assert "local" in unknown[1]


def test_exclusion_and_month_reconciliation():
    a = DATA["audit"]
    assert a["sampled"] == a["usable"] + sum(
        a[k]
        for k in ["invalid_required_fields", "duplicate_ids", "exact_duplicates", "near_duplicates"]
    )
    assert sum(a["monthly_usable"].values()) == a["usable"]
    con = duckdb.connect()
    con.register("e", pd.DataFrame(DATA["evidence"]))
    assert con.execute("SELECT SUM(n) FROM e").fetchone()[0] == a["usable"]
    counts = dict(con.execute("SELECT month,SUM(n) FROM e GROUP BY month").fetchall())
    assert counts == a["monthly_usable"]


def test_insight_denominators_and_evidence_references():
    e = pd.DataFrame(DATA["evidence"])
    for row in DATA["insights"]["issues"]:
        matched = e[(e["product"] == row["product"]) & (e["issue"] == row["issue"])]
        assert matched.n.sum() == row["n"]
        assert row["early"] + row["recent"] == row["n"]
        assert row["denominator"] == DATA["audit"]["usable"]
        expected = 100 * (
            row["recent"] / row["recent_denominator"] - row["early"] / row["early_denominator"]
        )
        assert abs(expected - row["change_pp"]) < 1e-12
    ids = {r["evidence_id"] for r in DATA["insights"]["issues"]}
    assert all(r["evidence_id"] in ids for r in DATA["insights"]["priorities"])


def test_confusion_and_review_reconcile():
    m = DATA["metrics"]
    matrix = np.array(m["confusion"])
    assert matrix.sum() == m["test_rows"]
    assert matrix.trace() == m["correct"]
    assert m["accepted"] + m["review"] == m["test_rows"]
    assert m["accepted_correct"] <= m["accepted"]
    assert sum(m["per_class"][label]["support"] for label in m["labels"]) == m["test_rows"]
    assert m["accuracy"] == m["correct"] / m["test_rows"]
    assert m["accepted_accuracy"] == m["accepted_correct"] / m["accepted"]


def test_public_downloads_match_reports():
    assert json.loads((ROOT / "site/metrics.json").read_text()) == DATA["metrics"]
    assert json.loads((ROOT / "reports/metrics.json").read_text()) == DATA["metrics"]
    assert (ROOT / "site/evidence.csv").read_bytes() == (ROOT / "reports/evidence.csv").read_bytes()


def test_routing_results_reconcile_to_sql_aggregate_counts():
    rows = pd.read_csv(ROOT / "reports/routing_counts.csv")
    test = rows[rows["split"] == "test"]
    m = DATA["metrics"]
    assert test.n.sum() == m["test_rows"]
    assert test.loc[test.observed == test.predicted, "n"].sum() == m["correct"]
    assert test.loc[test.accepted, "n"].sum() == m["accepted"]
    assert (
        test.loc[test.accepted & (test.observed == test.predicted), "n"].sum()
        == m["accepted_correct"]
    )
    assert test.loc[test.observed == m["majority"]["label"], "n"].sum() == m["majority"]["correct"]
    matrix = (
        test.groupby(["observed", "predicted"])
        .n.sum()
        .unstack(fill_value=0)
        .reindex(index=m["labels"], columns=m["labels"], fill_value=0)
    )
    np.testing.assert_array_equal(matrix.to_numpy(), m["confusion"])
    values = matrix.to_numpy()
    tp = np.diag(values)
    precision = np.divide(
        tp, values.sum(axis=0), out=np.zeros(len(tp)), where=values.sum(axis=0) != 0
    )
    recall = np.divide(tp, values.sum(axis=1), out=np.zeros(len(tp)), where=values.sum(axis=1) != 0)
    f1 = np.divide(
        2 * precision * recall,
        precision + recall,
        out=np.zeros(len(tp)),
        where=precision + recall != 0,
    )
    assert abs(f1.mean() - m["macro_f1"]) < 1e-12
    for i, label in enumerate(m["labels"]):
        assert abs(precision[i] - m["per_class"][label]["precision"]) < 1e-12
        assert abs(recall[i] - m["per_class"][label]["recall"]) < 1e-12
    for month in m["monthly"]:
        group = rows[rows.month == month["month"]]
        assert group.n.sum() == month["n"]
        assert group.loc[group.observed == group.predicted, "n"].sum() == month["correct"]


def test_public_privacy_allowlist():
    assert set(MODEL["vocabulary"]) <= SAFE
    assert all(
        set(row) == {"case", "observed", "predicted", "confidence", "reason"}
        for row in DATA["queue"]
    )
    assert not any(k in DATA for k in ["narratives", "Complaint ID", "Company", "ZIP code"])


def test_synthetic_split_boundaries_and_safe_preprocessing():
    assert [split_for(x) for x in ["2026-03-31", "2026-04-01", "2026-05-01", "2026-06-01"]] == [
        "train",
        "tune",
        "calibration",
        "test",
    ]
    assert safe_text("SYNTHETIC Ada email ada@example.test account 123456") == "email account"
    assert wilson(0, 0) is None
    assert wilson(50, 100)[0] < 0.5 < wilson(50, 100)[1]


def test_synthetic_duplicate_leakage_fixture():
    text = "synthetic fixture " + " ".join(sorted(SAFE)[:80])
    other = text + " additional"
    fixture = pd.DataFrame(
        {"text": [text, text, other, "synthetic mortgage lender balance escrow notice"]}
    )
    clean, audit = deduplicate(fixture)
    assert clean.index.tolist() == [0, 3]
    assert audit == {"exact_duplicates": 1, "near_duplicates": 1}


def test_synthetic_threshold_rejects_unsupported_accuracy():
    result = choose_threshold(np.repeat(0.8, 100), np.zeros(100, dtype=bool))
    assert result["threshold"] > 1 and result["accepted"] == 0
    assert map_labels(pd.Series(["known", "new"]), ["known"]).tolist() == ["known", "__UNSEEN__"]


def test_serving_bounded_readonly_routes():
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/").status_code == 200
    assert client.get("/api/predict?example=private-upload").status_code == 422
    assert client.post("/api/predict", json={"text": "private"}).status_code == 405
    for key, text in EXAMPLES.items():
        assert client.get("/api/predict", params={"example": key}).json() == predict(text)
        assert abs(sum(predict(text)["probabilities"]) - 1) < 1e-12
