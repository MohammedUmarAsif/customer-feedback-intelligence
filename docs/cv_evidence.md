# CV evidence

**[Customer Feedback Intelligence](https://MohammedUmarAsif.github.io/customer-feedback-intelligence/)**

- Analyzed 10,950 usable CFPB complaint narratives with Python and DuckDB; chronological text-only routing matched 71 labels per 100 versus 25 for a majority baseline, sending 50% to human review. Built an evidence-linked dashboard to prioritize debt-verification, account-management and purchase-dispute investigations.

## Traceability

Run `uv run python cv_evidence.py`. Counts come from `reports/audit.json`; routing correctness, majority comparison and review fraction come from `reports/metrics.json`. Rounded values describe the locked June 2026 test, not operational outcomes.

Measured: sample counts, exclusions, descriptive issue counts, chronological routing and review coverage. Prototype capabilities: interactive filters, safe browser inference, read-only review metadata, Docker runtime and CI. Not run: frozen embeddings, LoRA, prospective pilot, human adjudication, timed usability study or independent human reproduction. No claims of savings, adoption, users served or live complaint reduction.
