# CV evidence

**[Customer Feedback Intelligence](https://MohammedUmarAsif.github.io/customer-feedback-intelligence/)**

- Analyzed 10,950 public customer complaints with Python and SQL, identifying three investigation priorities. Built an interactive case study and text classifier achieving 70.8% accuracy versus a 25.4% baseline on unseen June data, with 49.9% of cases flagged for human review.

## Traceability

Run `uv run python cv_evidence.py`. Counts come from `reports/audit.json`; routing correctness, majority comparison and review fraction come from `reports/metrics.json`. Rounded values describe the locked June 2026 test, not operational outcomes.

Measured: sample counts, exclusions, descriptive issue counts, chronological routing and review coverage. Prototype capabilities: interactive filters, safe browser inference, read-only review metadata, Docker runtime and CI. Not run: frozen embeddings, LoRA, prospective pilot, human adjudication, timed usability study or independent human reproduction. No claims of savings, adoption, users served or live complaint reduction.
