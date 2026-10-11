# Research ledger

Sources inspected October 11, 2026. Primary documentation and research informed methods; all project scores come from its own frozen reports.

| Source | Adopted | Rejected or limited |
|---|---|---|
| [CFPB database](https://www.consumerfinance.gov/data-research/consumer-complaints/), [field reference](https://cfpb.github.io/api/ccdb/fields.html), [FOIA archive](https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/) | Official archives, receipt dates, consumer-selected labels, sampling and exposure caveats | No customer failure-rate or satisfaction interpretation |
| [Publication-policy change, August 2026](https://www.consumerfinance.gov/about-us/newsroom/the-cfpb-to-cease-discretionary-publication-of-complaint-narratives-and-visualizations/) | Historical archive acquisition replaces the old narrative API | No claim of a currently streaming narrative service |
| [Wang, Zhu and Chen, June 2026 preprint](https://arxiv.org/html/2606.22664v1) | Earlier-data development and later-data evaluation; distinguish structured context from text | Their monetary-relief target differs from routing. Relief is not severity or entitlement. Their scores are not ours. Temporal evaluation alone cannot rule out fitted-on-test representations or outcome-derived leakage; our vocabulary and selection are training-only. Mixed features can reflect reporting/provider patterns rather than causes. This is a preprint, not a claimed peer-reviewed result. |
| [DGE CX Spaces](https://www.dge.gov.ae/en/news/tamm-cx-spaces) | Feedback-to-decision workflow motivates the intended audience | No private TAMM data, endorsement, engagement or UAE/Japan performance |
| [scikit-learn text feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction), [logistic regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) | Sparse training-only TF-IDF, transparent classical routing baseline | Restricted generic vocabulary sacrifices expressive coverage for safer public artifacts |
| [MinHash LSH documentation](https://ekzhu.com/datasketch/lsh.html) | Seeded candidate screening with exact Jaccard decisions | LSH has false negatives; semantic duplicate prevention is not established |
| [Plotly JavaScript](https://plotly.com/javascript/getting-started/) | Pinned vendored chart library, real evidence values, responsive plots | No hosted Plotly paid service |
| [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) | Free public static dashboard, browser model inference | No server-side Python claim for the public host |

Optional future research: [LoRA, Hu et al., 2021](https://arxiv.org/abs/2106.09685) describes parameter-efficient adaptation. It is not a new 2026 method and has not been run here. Frozen embeddings may provide better semantic coverage, but would add a model/licence/compute review and require a new locked evaluation period. No BERTopic or PEFT dependency is added because neither is used in this release.
