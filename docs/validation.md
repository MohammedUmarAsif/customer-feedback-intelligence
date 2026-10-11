# Validation record

Checks executed by the Codex agent; independent human reproduction and case adjudication remain pending.

## Local analytical and application checks

- Official archive provenance, five compressed archive SHA-256 hashes, schema, acquisition UTC time, deterministic sample hash and monthly eligibility/cap counts recorded in `reports/manifest.json`.
- Frozen snapshot preparation and model rerun reproduced 12,000 sampled, 1,050 duplicate exclusions, 10,950 usable, and June correctness 1,281/1,810. No model choice was changed after opening June.
- Eleven pytest tests pass locally: exclusion/month reconciliation, SQL-derived priority denominators, confusion/review reconciliation, privacy allowlists, synthetic split/preprocessing/unknown-label/Wilson edge cases, synthetic exact/near duplicates, threshold rejection, bounded serving routes, training-only IDF/vocabulary and exact split leakage checks, and Python/sklearn export parity on 30 real held-out records.
- Public CI intentionally skips two tests needing private narratives; it does not claim to retrain or independently validate the real data snapshot.
- Ruff lint and formatting checks pass. Dependency lock is committed. A dependency deprecation warning in the FastAPI/Starlette HTTPX test adapter does not fail tests; no unchecked warning is reclassified as a model result.
- Fresh Chromium contexts at desktop 1440×1000 and mobile 390×844 verify product/issue filtering, reset, four synthetic routing flows, review-case filtering, chart rendering, no browser exceptions and no horizontal page overflow. Browser/Python confidence parity tolerance is 1e-10. Rendered screenshots were visually inspected for layout and readability.
- Raw narratives, source identifiers, companies, addresses, geographies and model pickles are excluded from public Git and Docker. Public coefficients use only 164 generic manually approved lexicon tokens learned from training. Anonymous review metadata is not a substitute for private case inspection.

## Container, CI and public deployment

Docker Desktop is installed but the local daemon could not start. No local successful Docker build/run is claimed. Linux GitHub Actions is configured to build the image, run its non-root CPU application, and check health and inference. Deployment and CI results will be recorded here after verification.

The public demo uses GitHub Pages, not a local URL and not a Python server. Public logged-out access and the same desktop/mobile flows will be checked in fresh contexts after deployment.

## Material limits

Near-duplicate LSH can miss matches and semantic paraphrases. Eligibility, consent/publication, equal monthly caps and template exclusion introduce selection. Narrative counts cannot establish failure rates without exposure. One locked month is insufficient for long-term stability; raw scores are not calibrated probabilities. The June accepted correctness is 89.9% despite the ≥90% May selection target. Prepaid-card recall is 0/22 and debt/credit-management recall is 1/18; do not rely on broad accuracy for those categories. No operational effect, financial saving, adoption, multilingual performance, frozen embeddings, LoRA, human adjudication or timed usability result is claimed.

Personal review before presentation: follow `docs/contributions.md`, reproduce a SQL count, inspect local model errors, and challenge at least one investigation hypothesis. Record actual reviews and unresolved questions there.

