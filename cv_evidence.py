"""Reproduce CV-facing numbers from frozen machine-readable reports."""

import json
from pathlib import Path

ROOT = Path(__file__).parent
LIVE = "https://MohammedUmarAsif.github.io/customer-feedback-intelligence/"


def render() -> str:
    audit = json.loads((ROOT / "reports/audit.json").read_text())
    model = json.loads((ROOT / "reports/metrics.json").read_text())
    bullet = (
        f"Analyzed {audit['usable']:,} usable CFPB complaint narratives with Python and DuckDB; "
        f"chronological text-only routing matched {100 * model['accuracy']:.0f} labels per 100 "
        f"versus {100 * model['majority']['accuracy']:.0f} for a majority baseline, sending "
        f"{100 * model['review'] / model['test_rows']:.0f}% to human review. Built an evidence-linked "
        "dashboard to prioritize debt-verification, account-management and purchase-dispute investigations."
    )
    assert 35 <= len(bullet.split()) <= 45
    return f"**[Customer Feedback Intelligence]({LIVE})**\n\n- {bullet}\n"


if __name__ == "__main__":
    text = render()
    (ROOT / "docs/cv_evidence.md").write_text(
        "# CV evidence\n\n" + text + "\n## Traceability\n\n"
        "Run `uv run python cv_evidence.py`. Counts come from `reports/audit.json`; routing correctness, majority comparison and review fraction come from `reports/metrics.json`. Rounded values describe the locked June 2026 test, not operational outcomes.\n\n"
        "Measured: sample counts, exclusions, descriptive issue counts, chronological routing and review coverage. Prototype capabilities: interactive filters, safe browser inference, read-only review metadata, Docker runtime and CI. Not run: frozen embeddings, LoRA, prospective pilot, human adjudication, timed usability study or independent human reproduction. No claims of savings, adoption, users served or live complaint reduction.\n",
        encoding="utf-8",
    )
    print(text)
