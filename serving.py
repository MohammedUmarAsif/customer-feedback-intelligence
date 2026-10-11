"""Read-only CPU runtime for the same aggregate dashboard and synthetic routing examples."""

import json
from pathlib import Path
from typing import Literal

import numpy as np
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
MODEL = json.loads((ROOT / "site/model.json").read_text())
EXAMPLES = {
    "credit": "My credit report includes an account I disputed. The credit bureau has not removed the error after my investigation request.",
    "mortgage": "My mortgage lender applied the monthly payment incorrectly. The escrow balance and interest statement are wrong.",
    "card": "My credit card statement shows an unauthorized purchase. I requested a refund and disputed the merchant charge.",
    "ambiguous": "I contacted customer service about the issue. The company sent a response but I still need an explanation.",
}


def predict(text: str) -> dict:
    """Inference from safe public weights; no pickled model or private data required."""
    import re

    counts = {}
    for word in re.findall(r"[a-z]{2,}", text.lower()):
        i = MODEL["vocabulary"].get(word)
        if i is not None:
            counts[i] = counts.get(i, 0) + 1
    x = np.zeros(len(MODEL["idf"]))
    for i, count in counts.items():
        x[i] = (1 + np.log(count)) * MODEL["idf"][i]
    norm = np.linalg.norm(x)
    if norm:
        x /= norm
    score = np.array(MODEL["coefficients"]) @ x + MODEL["intercept"]
    prob = np.exp(score - score.max())
    prob /= prob.sum()
    k = int(prob.argmax())
    return {
        "category": MODEL["classes"][k],
        "confidence": float(prob[k]),
        "review": bool(prob[k] < MODEL["threshold"]),
        "probabilities": prob.tolist(),
    }


app = FastAPI(title="Customer Feedback Intelligence", docs_url=None, redoc_url=None)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": "read-only public aggregates"}


@app.get("/api/predict")
def routing(example: Literal["credit", "mortgage", "card", "ambiguous"]) -> dict:
    return predict(EXAMPLES[example])


app.mount("/", StaticFiles(directory=ROOT / "site", html=True), name="dashboard")
