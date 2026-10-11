"""Frozen-sample audit, SQL evidence and chronological text-only routing experiment."""

import hashlib
import json
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from datasketch import MinHash, MinHashLSH
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score

from preprocessing import SAFE as SAFE
from preprocessing import normalized, safe_text

ROOT = Path(__file__).parent


def split_for(date: str) -> str:
    month = date[:7]
    return (
        "train"
        if month <= "2026-03"
        else {"2026-04": "tune", "2026-05": "calibration", "2026-06": "test"}[month]
    )


def map_labels(labels: pd.Series, supported: list[str]) -> pd.Series:
    return labels.where(labels.isin(supported), "__UNSEEN__")


def wilson(correct: int, total: int) -> list[float] | None:
    if not total:
        return None
    p = correct / total
    z = 1.96
    center = (p + z * z / (2 * total)) / (1 + z * z / total)
    half = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return [float(center - half), float(center + half)]


def deduplicate(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Keep first chronological record; approximate LSH candidates, exact Jaccard decision."""
    lsh = MinHashLSH(threshold=0.75, num_perm=128)
    exact, shingles, keep = set(), {}, []
    counts = {"exact_duplicates": 0, "near_duplicates": 0}
    for idx, row in frame.iterrows():
        words = normalized(row["text"]).split()
        norm = " ".join(words)
        digest = hashlib.sha256(norm.encode()).hexdigest()
        if digest in exact:
            counts["exact_duplicates"] += 1
            continue
        grams = {" ".join(words[i : i + 5]) for i in range(max(1, len(words) - 4))}
        mh = MinHash(num_perm=128, seed=42)
        mh.update_batch([g.encode() for g in sorted(grams)])
        candidates = lsh.query(mh)
        duplicate = any(
            len(grams & shingles[k]) / len(grams | shingles[k]) >= 0.85 for k in candidates
        )
        if duplicate:
            counts["near_duplicates"] += 1
            continue
        key = str(idx)
        exact.add(digest)
        shingles[key] = grams
        lsh.insert(key, mh)
        keep.append(idx)
    return frame.loc[keep].copy(), counts


def choose_threshold(prob: np.ndarray, correct: np.ndarray) -> dict:
    candidates = []
    for threshold in np.arange(0.35, 0.96, 0.01):
        accepted = prob >= threshold
        count = int(accepted.sum())
        if count >= 50 and correct[accepted].mean() >= 0.90:
            candidates.append(
                {
                    "threshold": float(threshold),
                    "accepted": count,
                    "correct": int(correct[accepted].sum()),
                    "n": len(correct),
                }
            )
    return (
        max(candidates, key=lambda x: x["accepted"])
        if candidates
        else {"threshold": 1.01, "accepted": 0, "correct": 0, "n": len(correct)}
    )


def build() -> None:
    reports = ROOT / "reports"
    manifest = json.loads((reports / "manifest.json").read_text())
    raw = pd.read_parquet(ROOT / "data/private/sample.parquet")
    assert (
        hashlib.file_digest((ROOT / "data/private/sample.parquet").open("rb"), "sha256").hexdigest()
        == manifest["sample_sha256"]
    )
    frame = raw.rename(
        columns={
            "Date received": "date",
            "Product": "product",
            "Issue": "issue",
            "Consumer complaint narrative": "text",
            "Submitted via": "channel",
            "Timely response?": "timely",
            "Complaint ID": "id",
        }
    )[["date", "product", "issue", "text", "channel", "timely", "id", "month"]].copy()
    dates = pd.to_datetime(frame["date"], errors="coerce")
    invalid = (
        dates.isna()
        | ~dates.between("2026-01-01", "2026-06-30")
        | (frame["product"].str.strip() == "")
        | (frame["issue"].str.strip() == "")
        | (frame["text"].str.len() < 40)
        | (frame["id"].str.strip() == "")
    )
    invalid_count = int(invalid.sum())
    frame = frame.loc[~invalid].sort_values(["date", "id"]).reset_index(drop=True)
    duplicate_ids = int(frame["id"].duplicated().sum())
    frame = frame.drop_duplicates("id")
    frame, duplicate_counts = deduplicate(frame)
    frame["split"] = frame["date"].map(split_for)
    frame.to_parquet(ROOT / "data/private/clean.parquet", index=False)
    audit = {
        "sampled": len(raw),
        "invalid_required_fields": invalid_count,
        "duplicate_ids": duplicate_ids,
        **duplicate_counts,
        "usable": len(frame),
        "split_counts": frame["split"].value_counts().to_dict(),
        "missing_fields": {
            c: int((raw[c] == "").sum())
            for c in raw.columns
            if c not in ["Consumer complaint narrative", "Complaint ID", "sample_key"]
        },
        "monthly_usable": frame["month"].value_counts().sort_index().to_dict(),
    }
    assert audit["sampled"] == audit["usable"] + invalid_count + duplicate_ids + sum(
        duplicate_counts.values()
    )
    private_db = ROOT / "data/private/analysis.duckdb"
    con = duckdb.connect(str(private_db))
    con.register("prepared", frame.drop(columns=["text", "id"]))
    con.execute("""CREATE OR REPLACE TABLE complaints AS
        SELECT CAST(date AS DATE) AS date, CAST(product AS VARCHAR) AS product,
        CAST(issue AS VARCHAR) AS issue, CAST(channel AS VARCHAR) AS channel,
        CAST(timely AS VARCHAR) AS timely, CAST(month AS VARCHAR) AS month,
        CAST(split AS VARCHAR) AS split FROM prepared""")
    evidence = con.execute((ROOT / "sql/metrics.sql").read_text()).df()
    evidence.to_csv(reports / "evidence.csv", index=False)
    channels = (
        con.execute(
            "SELECT channel, COUNT(*)::INTEGER n FROM complaints GROUP BY channel ORDER BY n DESC"
        )
        .df()
        .to_dict("records")
    )
    timely = (
        con.execute(
            "SELECT COUNT(*) FILTER(WHERE timely='Yes')::INTEGER AS timely_yes, COUNT(*) FILTER(WHERE timely IN ('Yes','No'))::INTEGER known, COUNT(*)::INTEGER total FROM complaints"
        )
        .df()
        .to_dict("records")[0]
    )
    con.close()
    train = frame[frame["split"] == "train"]
    supported = sorted(train["product"].value_counts()[lambda x: x >= 30].index)
    train = train[train["product"].isin(supported)]
    # Only the manually approved generic lexicon can become a public model feature.
    vectorizer = TfidfVectorizer(preprocessor=safe_text, min_df=3, sublinear_tf=True)
    x_train = vectorizer.fit_transform(train["text"])
    tune = frame[frame["split"] == "tune"]
    candidates = []
    for c in [0.3, 1.0, 3.0]:
        model = LogisticRegression(C=c, max_iter=1000, random_state=42)
        model.fit(x_train, train["product"])
        pred = model.predict(vectorizer.transform(tune["text"]))
        candidates.append(
            (
                f1_score(tune["product"], pred, labels=supported, average="macro", zero_division=0),
                c,
                model,
            )
        )
    _, best_c, model = max(candidates, key=lambda x: (x[0], -x[1]))
    cal = frame[frame["split"] == "calibration"]
    cal_prob = model.predict_proba(vectorizer.transform(cal["text"]))
    cal_pred = model.classes_[cal_prob.argmax(axis=1)]
    selection = choose_threshold(cal_prob.max(axis=1), cal_pred == cal["product"].to_numpy())
    # The locked test is accessed only after vocabulary, model and threshold are fixed.
    test = frame[frame["split"] == "test"]
    prob = model.predict_proba(vectorizer.transform(test["text"]))
    pred = model.classes_[prob.argmax(axis=1)]
    truth = map_labels(test["product"], supported).to_numpy()
    labels = supported + (["__UNSEEN__"] if (truth == "__UNSEEN__").any() else [])
    correct = pred == truth
    accepted = prob.max(axis=1) >= selection["threshold"]
    majority = train["product"].mode()[0]
    metrics = {
        "task": "observed product from narrative only",
        "labels": labels,
        "train_rows": len(train),
        "unsupported_train_rows": audit["split_counts"]["train"] - len(train),
        "test_rows": len(test),
        "test_unseen_rows": int((truth == "__UNSEEN__").sum()),
        "correct": int(correct.sum()),
        "accuracy": float(correct.mean()),
        "macro_f1": float(f1_score(truth, pred, labels=labels, average="macro", zero_division=0)),
        "majority": {
            "label": majority,
            "correct": int((truth == majority).sum()),
            "accuracy": float((truth == majority).mean()),
            "macro_f1": float(
                f1_score(
                    truth,
                    np.repeat(majority, len(test)),
                    labels=labels,
                    average="macro",
                    zero_division=0,
                )
            ),
        },
        "C": best_c,
        "tuning": [{"C": c, "macro_f1": score} for score, c, _ in candidates],
        "vocabulary_size": len(vectorizer.vocabulary_),
        "threshold_selection": selection,
        "accepted": int(accepted.sum()),
        "accepted_correct": int(correct[accepted].sum()),
        "review": int((~accepted).sum()),
        "accepted_accuracy": float(correct[accepted].mean()) if accepted.any() else None,
        "accepted_wilson": wilson(int(correct[accepted].sum()), int(accepted.sum())),
        "accuracy_wilson": wilson(int(correct.sum()), len(test)),
        "confusion": confusion_matrix(truth, pred, labels=labels).tolist(),
        "per_class": classification_report(
            truth, pred, labels=labels, output_dict=True, zero_division=0
        ),
        "monthly": [],
    }
    evaluation_parts = []
    for month, group in frame.groupby("month"):
        predictions = model.predict(vectorizer.transform(group["text"]))
        monthly_prob = model.predict_proba(vectorizer.transform(group["text"])).max(axis=1)
        evaluation_parts.append(
            pd.DataFrame(
                {
                    "month": month,
                    "split": group["split"].iloc[0],
                    "observed": map_labels(group["product"], supported).to_numpy(),
                    "predicted": predictions,
                    "accepted": monthly_prob >= selection["threshold"],
                }
            )
        )
        metrics["monthly"].append(
            {
                "month": month,
                "split": group["split"].iloc[0],
                "n": len(group),
                "correct": int((predictions == group["product"]).sum()),
                "macro_f1": float(
                    f1_score(
                        group["product"],
                        predictions,
                        labels=supported,
                        average="macro",
                        zero_division=0,
                    )
                ),
            }
        )
    evaluation = pd.concat(evaluation_parts, ignore_index=True)
    con = duckdb.connect(str(private_db))
    con.register("evaluation", evaluation)
    con.execute("CREATE OR REPLACE TABLE routing_evaluation AS SELECT * FROM evaluation")
    routing_counts = con.execute((ROOT / "sql/routing.sql").read_text()).df()
    routing_counts.to_csv(reports / "routing_counts.csv", index=False)
    con.close()
    # No identifiers, dates, narratives or company details in the public review queue.
    queue = [
        {
            "case": f"JUNE-{i + 1:04}",
            "observed": str(y),
            "predicted": str(p),
            "confidence": float(conf),
            "reason": "low model confidence",
        }
        for i, (y, p, conf, accept) in enumerate(
            zip(truth, pred, prob.max(axis=1), accepted, strict=True)
        )
        if not accept
    ]
    public_model = {
        "vocabulary": vectorizer.vocabulary_,
        "idf": vectorizer.idf_.tolist(),
        "coefficients": model.coef_.tolist(),
        "intercept": model.intercept_.tolist(),
        "classes": model.classes_.tolist(),
        "threshold": selection["threshold"],
        "max_chars": 3000,
    }
    joblib.dump((vectorizer, model, selection["threshold"]), ROOT / "data/private/model.joblib")
    bundle = {
        "audit": audit,
        "metrics": metrics,
        "manifest": manifest,
        "evidence": evidence.to_dict("records"),
        "channels": channels,
        "timely": timely,
        "queue": sorted(queue, key=lambda x: x["confidence"])[:100],
        "queue_total": len(queue),
    }
    (ROOT / "site").mkdir(exist_ok=True)
    for path, value in [
        (reports / "audit.json", audit),
        (reports / "metrics.json", metrics),
        (ROOT / "site/data.json", bundle),
        (ROOT / "site/model.json", public_model),
    ]:
        path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "audit": audit,
                "metrics": {
                    k: metrics[k]
                    for k in [
                        "test_rows",
                        "accuracy",
                        "macro_f1",
                        "accepted",
                        "accepted_accuracy",
                        "review",
                    ]
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    build()
