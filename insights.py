"""SQL-backed transparent issue priorities and a deterministic decision brief."""

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from pipeline import wilson

ROOT = Path(__file__).parent


def priority_guidance(product: str, issue: str) -> tuple[str, str]:
    """Attach editorial guidance to the evidence identity, never its current rank."""
    guidance = {
        ("Debt collection", "Attempts to collect debt not owed"): (
            "Investigate debt-ownership verification and the evidence provided before collection attempts.",
            "Review a local random sample for mistaken identity, disputed balance, and missing ownership documentation; compare against account-level verification logs.",
        ),
        ("Checking or savings account", "Managing an account"): (
            "Investigate account-management handoffs, access restrictions, and the clarity of customer status updates.",
            "Code a local random sample into access, balance, and service-status reasons; compare handoff times and repeat contacts with operational logs.",
        ),
        ("Credit card", "Problem with a purchase shown on your statement"): (
            "Investigate the purchase-dispute journey and whether evidence requirements are clear.",
            "Separate unauthorized purchases from merchant disputes in a local sample; check evidence requests, response time, and repeat contacts against transaction exposure.",
        ),
    }
    return guidance.get(
        (product, issue),
        (
            "Audit the handling and dispute journey for this recurring issue.",
            "Have a human review a bounded random case sample locally; compare operational contact reasons and transaction exposure before testing a process change.",
        ),
    )


def build_insights() -> None:
    bundle = json.loads((ROOT / "site/data.json").read_text())
    evidence = pd.read_csv(ROOT / "reports/evidence.csv")
    con = duckdb.connect()
    con.register("evidence", evidence)
    query = """
        SELECT product, issue, SUM(n)::INTEGER n,
        SUM(n) FILTER(WHERE month <= '2026-03')::INTEGER early,
        SUM(n) FILTER(WHERE month >= '2026-04')::INTEGER recent
        FROM evidence GROUP BY product, issue ORDER BY n DESC, product, issue
    """
    rows = con.execute(query).df().fillna(0).to_dict("records")
    denominators = (
        con.execute(
            "SELECT SUM(n) FILTER(WHERE month <= '2026-03')::INTEGER early, SUM(n) FILTER(WHERE month >= '2026-04')::INTEGER recent, SUM(n)::INTEGER total FROM evidence"
        )
        .df()
        .to_dict("records")[0]
    )
    con.close()
    for i, row in enumerate(rows):
        row["evidence_id"] = f"E{i + 1:03}"
        row["early_denominator"] = denominators["early"]
        row["recent_denominator"] = denominators["recent"]
        row["denominator"] = denominators["total"]
        row["share"] = row["n"] / denominators["total"]
        row["change_pp"] = 100 * (
            row["recent"] / denominators["recent"] - row["early"] / denominators["early"]
        )
        row["share_wilson"] = wilson(row["n"], denominators["total"])
        # Descriptive month-block resampling, only three observed months per period.
        monthly = (
            evidence[(evidence["product"] == row["product"]) & (evidence["issue"] == row["issue"])]
            .groupby("month")
            .n.sum()
        )
        months = sorted(bundle["audit"]["monthly_usable"])
        counts = np.array([int(monthly.get(m, 0)) for m in months])
        totals = np.array([bundle["audit"]["monthly_usable"][m] for m in months])
        rng = np.random.default_rng(42)
        boot = []
        for _ in range(1000):
            early = rng.integers(0, 3, size=3)
            recent = rng.integers(3, 6, size=3)
            boot.append(
                100
                * (
                    counts[recent].sum() / totals[recent].sum()
                    - counts[early].sum() / totals[early].sum()
                )
            )
        row["change_block_interval"] = np.quantile(boot, [0.025, 0.975]).tolist()
        row["evidence_quality"] = "Sample association; selected narratives; no exposure denominator"
    priorities = rows[:3]
    for row in priorities:
        row["recommendation"], row["next_check"] = priority_guidance(row["product"], row["issue"])
        row["alternative"] = (
            "Reporting campaigns, narrative-consent differences, repeated templates, or product mix could explain the volume."
        )
        row["hypothesis"] = (
            "Clearer evidence requirements and status updates may reduce repeat contacts; test prospectively with an exposure denominator and a comparison group."
        )
    report = {
        "denominators": denominators,
        "issues": rows,
        "priorities": priorities,
        "change_ranking": sorted(
            [r for r in rows if r["n"] >= 50], key=lambda r: (-r["change_pp"], r["evidence_id"])
        )[:5],
        "ranking_policy": "Total sampled volume descending; change displayed separately. No causal or severity interpretation.",
    }
    (ROOT / "reports/insights.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bundle["insights"] = report
    (ROOT / "site/data.json").write_text(
        json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8"
    )
    brief = "# Decision brief\n\nThese are investigation hypotheses from a self-selected, unweighted historical narrative sample, not proven root causes. Priorities rank total sampled volume; change and evidence quality remain separate.\n\n"
    for row in priorities:
        brief += f"## {row['evidence_id']}: {row['issue']}\n\nProduct: {row['product']}. {row['n']:,}/{row['denominator']:,} usable sampled narratives ({row['share']:.1%}). April–June versus January–March: {row['change_pp']:+.2f} percentage points, using {row['recent']}/{row['recent_denominator']} and {row['early']}/{row['early_denominator']}.\n\n{row['recommendation']} Alternative explanation: {row['alternative']} Next check: {row['next_check']} Testable intervention: {row['hypothesis']}\n\n"
    brief += "## Pilot design, not yet run\n\nCollect prospective contact counts, transaction/customer exposure, product mix and independently reviewed complaint reasons. Randomize an eligible operational unit to clearer evidence/status messaging versus current practice where feasible. Pre-register a repeat-contact proportion, assignment unit, follow-up window and guardrails. Compare groups with cluster-aware uncertainty and monitor access/equity. No savings or reductions have been measured.\n\n## Evidence and uncertainty\n\nReconcile `reports/evidence.csv` using `sql/metrics.sql`; `reports/insights.json` holds all numerators and denominators. Wilson intervals are descriptive binomial intervals with independence caveats. Month-block bootstrap intervals use just three months per period and do not justify significance or seasonality claims. Volume rankings and change rankings differ; inspect both before selecting a pilot.\n"
    (ROOT / "docs/decision_brief.md").write_text(brief, encoding="utf-8")
    print([(r["evidence_id"], r["n"], r["change_pp"]) for r in priorities])


if __name__ == "__main__":
    build_insights()
