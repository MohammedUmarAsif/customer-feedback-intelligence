# Validation record

Checks executed by the Codex agent; independent human reproduction and case adjudication remain pending.

## Local analytical and application checks

- Official archive provenance, five compressed archive SHA-256 hashes, schema, acquisition UTC time, deterministic sample hash and monthly eligibility/cap counts recorded in `reports/manifest.json`.
- Frozen snapshot preparation and model rerun reproduced 12,000 sampled, 1,050 duplicate exclusions, 10,950 usable, and June correctness 1,281/1,810. No model choice was changed after opening June.
- Twelve pytest tests pass locally: exclusion/month reconciliation, SQL-derived priority denominators, confusion/review reconciliation, public download consistency, SQL routing-count reconciliation, privacy allowlists, synthetic split/preprocessing/unknown-label/Wilson edge cases, synthetic exact/near duplicates, threshold rejection, bounded serving routes, training-only IDF/vocabulary and exact split leakage checks, and Python/sklearn export parity on 30 real held-out records.
- Public CI intentionally skips two tests needing private narratives; it does not claim to retrain or independently validate the real data snapshot.
- Ruff lint and formatting checks pass. Dependency lock is committed. A dependency deprecation warning in the FastAPI/Starlette HTTPX test adapter does not fail tests; no unchecked warning is reclassified as a model result.
- Fresh Chromium contexts at desktop 1440×1000 and mobile 390×844 verify product/issue filtering, reset, four synthetic routing flows, review-case filtering, chart rendering, no browser exceptions and no horizontal page overflow. Browser/Python confidence parity tolerance is 1e-10. Rendered screenshots were visually inspected for layout and readability.
- Raw narratives, source identifiers, companies, addresses, geographies and model pickles are excluded from public Git and Docker. Public coefficients use only 164 generic manually approved lexicon tokens learned from training. Anonymous review metadata is not a substitute for private case inspection.

## Container, CI and public deployment

Docker Desktop is installed but the local daemon could not start. No local successful Docker build/run is claimed. [Linux GitHub Actions run 38170474084](https://github.com/MohammedUmarAsif/customer-feedback-intelligence/actions/runs/38170474084) succeeded, including a real Docker build, container launch, health endpoint and bounded inference check. It also passed Ruff, public-data tests, the publication gate and rendered browser flows. The first CI attempt caught a publication-check lint issue; it was corrected and the subsequent run succeeded. No failed check is hidden as a successful validation.

The public demo is [GitHub Pages](https://mohammedumarasif.github.io/customer-feedback-intelligence/), not a local URL and not a Python server. [Deployment run 38170474067](https://github.com/MohammedUmarAsif/customer-feedback-intelligence/actions/runs/38170474067) succeeded. Public access returned HTTP 200 in fresh Chromium contexts without stored credentials. The same desktop/mobile flows passed on the public URL; evidence is saved in `reports/public_ui_validation.json`. Screenshots show safe aggregate data and synthetic examples only. The final SQL extension adds aggregate routing counts, whose confusion totals, precision/recall/macro-F1, acceptance counts and monthly counts are checked against the model report.

## Material limits

Near-duplicate LSH can miss matches and semantic paraphrases. Eligibility, consent/publication, equal monthly caps and template exclusion introduce selection. Narrative counts cannot establish failure rates without exposure. One locked month is insufficient for long-term stability; raw scores are not calibrated probabilities. The June accepted correctness is 89.9% despite the ≥90% May selection target. Prepaid-card recall is 0/22 and debt/credit-management recall is 1/18; do not rely on broad accuracy for those categories. No operational effect, financial saving, adoption, multilingual performance, frozen embeddings, LoRA, human adjudication or timed usability result is claimed.

Personal review before presentation: follow `docs/contributions.md`, reproduce a SQL count, inspect local model errors, and challenge at least one investigation hypothesis. Record actual reviews and unresolved questions there.


## Guided-story release — 12 October 2026

The presentation now starts with the customer-service problem, then findings, interactive evidence, a model comparison, and a validation plan. The frozen analytical results are unchanged. Thirteen tests pass locally, including the new recommendation-identity regression test; public CI passes eleven and skips the two private-data checks.

[Story validation run 38175198387](https://github.com/MohammedUmarAsif/customer-feedback-intelligence/actions/runs/38175198387) passed Ruff, pytest, the publication gate, desktop 1440×1000 and mobile 390×844 browser flows, exported-model parity, missing-data/model states, and a real Linux Docker build/run. The three finding links now select their matching product and issue; queue pagination reaches the exported preview cases. Current visual evidence is in `docs/audit/` and the machine-readable browser result in `reports/story_ui_validation.json`.

The live page was checked for filter handoffs, four model examples and queue pagination, with no recorded browser errors. Exact-size screenshot evidence comes from fresh Linux Chromium contexts. Desktop and mobile screenshots were visually inspected; no full screen-reader or usability-study result is claimed.

The chart library was removed from the page and repository. Core uncompressed page assets are approximately 329 KB, versus 1.49 MB before this release (about 78% smaller). This is a deterministic asset-size comparison; network timings and Core Web Vitals were not benchmarked.

## Five-scene refinement, 12 October 2026

The current screenshots and `reports/story_ui_validation.json` come from local fresh Chromium contexts at desktop 1440×1000 and mobile 390×844. Checks passed for finding-bar handoffs, chart filters, 100-dot rounded counts (45 correct, 5 incorrect above cutoff, 50 review), three example buttons, all four model predictions versus Python, queue pagination and missing-file recovery. No JavaScript errors or horizontal page overflow occurred. Thirteen local pytest tests and Ruff checks passed. The data and model were not refitted. Primary archive/research links are provided in the relevant disclosures; internal section and repository evidence links were reconciled against the checkout.

## Dashboard-first redesign, 12 October 2026

The opening now contains the actual linked count and monthly-trend dashboard, a compact summary strip, and accuracy/review panels. A shorter introduction replaces the earlier workflow hero. The problem, data/methods, results and discussion follow as four chapters; technical disclosures and source links remain available. The model and data were not refitted.

Local validation passed at 1440×1000 and 390×844, including a desktop first-viewport chart-position assertion, readable mobile heading, three methods/source disclosures, finding handoffs, filters, 100-dot counts, example buttons, inference parity, review pagination, load-failure recovery, no page overflow and no JavaScript errors. Thirteen pytest tests, Ruff and the publication gate passed. All 33 section, download and repository evidence links were reconciled against the checkout; external primary references were previously inspected. Screenshots were visually reviewed. No usability-study or operational improvement claim is made.
