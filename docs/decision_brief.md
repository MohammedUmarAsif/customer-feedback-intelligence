# Decision brief

These are investigation hypotheses from a self-selected, unweighted historical narrative sample, not proven root causes. Priorities rank total sampled volume; change and evidence quality remain separate.

## E001: Attempts to collect debt not owed

Product: Debt collection. 1,417/10,950 usable sampled narratives (12.9%). April–June versus January–March: -1.40 percentage points, using 671/5481 and 746/5469.

Investigate debt-ownership verification and the evidence provided before collection attempts. Alternative explanation: Reporting campaigns, narrative-consent differences, repeated templates, or product mix could explain the volume. Next check: Review a local random sample for mistaken identity, disputed balance, and missing ownership documentation; compare against account-level verification logs. Testable intervention: Clearer evidence requirements and status updates may reduce repeat contacts; test prospectively with an exposure denominator and a comparison group.

## E002: Managing an account

Product: Checking or savings account. 1,141/10,950 usable sampled narratives (10.4%). April–June versus January–March: +0.47 percentage points, using 584/5481 and 557/5469.

Investigate account-management handoffs, access restrictions, and the clarity of customer status updates. Alternative explanation: Reporting campaigns, narrative-consent differences, repeated templates, or product mix could explain the volume. Next check: Code a local random sample into access, balance, and service-status reasons; compare handoff times and repeat contacts with operational logs. Testable intervention: Clearer evidence requirements and status updates may reduce repeat contacts; test prospectively with an exposure denominator and a comparison group.

## E003: Problem with a purchase shown on your statement

Product: Credit card. 698/10,950 usable sampled narratives (6.4%). April–June versus January–March: +0.28 percentage points, using 357/5481 and 341/5469.

Investigate the purchase-dispute journey and whether evidence requirements are clear. Alternative explanation: Reporting campaigns, narrative-consent differences, repeated templates, or product mix could explain the volume. Next check: Separate unauthorized purchases from merchant disputes in a local sample; check evidence requests, response time, and repeat contacts against transaction exposure. Testable intervention: Clearer evidence requirements and status updates may reduce repeat contacts; test prospectively with an exposure denominator and a comparison group.

## Pilot design, not yet run

Collect prospective contact counts, transaction/customer exposure, product mix and independently reviewed complaint reasons. Randomize an eligible operational unit to clearer evidence/status messaging versus current practice where feasible. Pre-register a repeat-contact proportion, assignment unit, follow-up window and guardrails. Compare groups with cluster-aware uncertainty and monitor access/equity. No savings or reductions have been measured.

## Evidence and uncertainty

Reconcile `reports/evidence.csv` using `sql/metrics.sql`; `reports/insights.json` holds all numerators and denominators. Wilson intervals are descriptive binomial intervals with independence caveats. Month-block bootstrap intervals use just three months per period and do not justify significance or seasonality claims. Volume rankings and change rankings differ; inspect both before selecting a pilot.
