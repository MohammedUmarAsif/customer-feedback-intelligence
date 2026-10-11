# A plain-language walkthrough

**The problem.** A support team needs to respond to individual customers and notice when the same problem keeps appearing. This study asks two questions: what deserves investigation, and can a model help sort new messages?

**The data.** These are real public complaints about US financial products. We sampled 12,000 written accounts across six months and removed 1,050 repeated or very similar entries. No private complaint text is displayed on the website.

**The finding.** The largest product-and-issue pair contains 1,417 complaints about attempts to collect money people say they do not owe. That suggests investigating how ownership is verified. It does not establish why the problem happened. Click “Explore this issue” to select the matching product and issue in the chart.

**The experiment.** A simple baseline always predicts the most common category. It matches 25.4% of the June labels. A model trained on words matches 70.8%. June data was held aside during development, so this comparison tests later examples rather than memorized training cases.

**The trade-off.** About half the June messages receive low scores and are flagged for review. Among the higher-score half, 89.9% match the published category. Show the home-loan example, then the credit-report mistake: a model can help without being trusted blindly.

**The result and next step.** The delivered result is a reproducible investigation workflow and an evaluated classifier. The next step would be a human case review and a controlled service pilot. Reduced repeat contacts, faster handling, and cost savings have not been measured.

**Research connection.** Like comparing models in an environmental-science experiment, compare against a baseline, separate development and testing, inspect errors, and ask whether any improvement changes a practical decision. Domain expertise is needed to interpret both the data and the result.
