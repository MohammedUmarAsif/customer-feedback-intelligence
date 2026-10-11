# Experiment ledger

Executed by the Codex agent on October 11, 2026. Human reproduction remains pending. Full numeric results: `reports/metrics.json`; archive and sample hashes: `reports/manifest.json`.

| Experiment | Status | Selection data | Locked evaluation |
|---|---|---|---|
| Majority product | Run | January–March modal training category, Debt collection | June: 460/1,810 correct, macro-F1 0.03684 |
| Restricted-lexicon TF-IDF/logistic regression | Run | Training vocabulary/IDF and weights; April selects C=1 from 0.3, 1, 3 | June: 1,281/1,810 correct, macro-F1 0.53129 |
| Review threshold | Run | May: threshold 0.66; 832/922 accepted cases correct out of 1,803 total | June: 815/907 accepted cases correct; 903/1,810 require review |
| Exported CPU/browser model | Run | Exact numerical export, no retraining | Python/sklearn parity on 30 real test records; browser/Python parity on four synthetic examples |
| Frozen embeddings | Not run | Requires model/licence selection and a fresh future locked test | No score claimed |
| LoRA | Not run | Optional follow-up; no training configuration or result advertised | No score claimed |
| Operational intervention | Not run | Prospective exposure/log data required | No impact or savings claimed |

Model selection was frozen before June access. Reruns after packaging/refactoring retain the same algorithm, features, hyperparameters and threshold and reproduce the same metrics. June has now been opened; future experiments require a new untouched time period. Seeds are 42 for sampling, MinHash and logistic regression. Dependency versions are locked; Linux/Windows numeric comparisons permit 1e-10 tolerance. Private narratives and pickled models are never public artifacts.
