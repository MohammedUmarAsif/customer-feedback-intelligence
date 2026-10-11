"use strict";
let data, model;
const $ = (id) => document.getElementById(id),
  fmt = (n) => Number(n).toLocaleString("en-US"),
  pct = (n, d) => (d ? `${((100 * n) / d).toFixed(1)}%` : "Unavailable");
const esc = (s) =>
  String(s).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const table = (headers, rows) =>
  `<table><thead><tr>${headers.map((h) => `<th scope="col">${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((c) => `<td>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
const metric = (value, label, note) =>
  `<div class="metric"><strong>${esc(value)}</strong><span>${esc(label)}</span><small>${esc(note)}</small></div>`;
const examples = {
  credit:
    "My credit report includes an account I disputed. The credit bureau has not removed the error after my investigation request.",
  mortgage:
    "My mortgage lender applied the monthly payment incorrectly. The escrow balance and interest statement are wrong.",
  card: "My credit card statement shows an unauthorized purchase. I requested a refund and disputed the merchant charge.",
  ambiguous:
    "I contacted customer service about the issue. The company sent a response but I still need an explanation.",
};
function showExample() {
  $("example-text").textContent = examples[$("example").value];
  $("prediction").textContent =
    "Select Predict routing to see the model output.";
}
function showQueue() {
  const rows = data.queue
    .filter(
      (r) => $("queue-filter").value !== "errors" || r.observed !== r.predicted,
    )
    .slice(0, 8);
  $("queue").innerHTML = rows.length
    ? table(
        ["Case", "Observed", "Predicted", "Confidence"],
        rows.map((r) => [
          r.case,
          r.observed,
          r.predicted,
          r.confidence.toFixed(3),
        ]),
      )
    : "<p>No cases match this view.</p>";
}
function fillIssues() {
  const product = $("product").value;
  const issues = [
    ...new Set(
      data.evidence
        .filter((r) => !product || r.product === product)
        .map((r) => r.issue),
    ),
  ].sort();
  $("issue").innerHTML =
    '<option value="">Top issues by volume</option>' +
    issues.map((i) => `<option value="${esc(i)}">${esc(i)}</option>`).join("");
}
function showTrends() {
  const product = $("product").value,
    issue = $("issue").value;
  const base = data.evidence.filter((r) => !product || r.product === product),
    months = Object.keys(data.audit.monthly_usable).sort(),
    totals = {},
    counts = {};
  for (const row of base) {
    totals[row.month] = (totals[row.month] || 0) + row.n;
    counts[row.issue] = (counts[row.issue] || 0) + row.n;
  }
  const ranked = Object.keys(counts).sort(
      (a, b) => counts[b] - counts[a] || a.localeCompare(b),
    ),
    chosen = issue ? [issue] : ranked.slice(0, 3),
    denom = Object.values(totals).reduce((a, b) => a + b, 0);
  $("filter-summary").textContent =
    `${product || "All products"} · ${fmt(denom)} usable sampled narratives, January–June 2026. Lines show ${issue ? "the selected issue" : "the three highest-volume issues"}.`;
  const monthRows = [],
    traces = chosen.map((name, k) => {
      const numerators = months.map((m) =>
        base
          .filter((r) => r.month === m && r.issue === name)
          .reduce((sum, r) => sum + r.n, 0),
      );
      months.forEach((m, i) =>
        monthRows.push([
          m,
          name,
          fmt(numerators[i]),
          fmt(totals[m] || 0),
          pct(numerators[i], totals[m]),
        ]),
      );
      return {
        x: months,
        y: numerators.map((n, i) =>
          totals[months[i]] ? (100 * n) / totals[months[i]] : null,
        ),
        name,
        type: "scatter",
        mode: "lines+markers",
        line: { color: ["#006b67", "#395c87", "#965014"][k % 3], width: 3 },
        customdata: numerators.map((n, i) => [n, totals[months[i]] || 0]),
        hovertemplate:
          "%{x}<br>%{y:.1f}% (%{customdata[0]}/%{customdata[1]})<extra>%{fullData.name}</extra>",
      };
    });
  if (window.Plotly)
    Plotly.react(
      "trend-chart",
      traces,
      {
        margin: { t: 20, r: 20, b: 100, l: 55 },
        height: window.innerWidth < 760 ? 320 : 360,
        paper_bgcolor: "#fff",
        plot_bgcolor: "#fff",
        font: { family: "Segoe UI, Arial", color: "#182b32" },
        yaxis: {
          title: { text: "Share of selected monthly sample (%)" },
          rangemode: "tozero",
        },
        xaxis: { type: "category" },
        legend: { orientation: "h", y: -0.28, font: { size: 11 } },
      },
      { responsive: true, displayModeBar: false },
    );
  else
    $("trend-chart").textContent =
      "Chart unavailable. Use the monthly evidence table below.";
  $("trend-table").innerHTML = table(
    ["Month", "Issue", "Count", "Monthly denominator", "Share"],
    monthRows,
  );
  $("issue-table").innerHTML = table(
    ["Recurring issue", "Count", "Share of selected sample"],
    ranked
      .slice(0, 10)
      .map((i) => [
        i,
        fmt(counts[i]),
        `${pct(counts[i], denom)} (${fmt(counts[i])}/${fmt(denom)})`,
      ]),
  );
}
function render() {
  $("content").hidden = false;
  const a = data.audit,
    m = data.metrics;
  $("headline").innerHTML =
    metric(
      fmt(a.usable),
      "Usable narratives",
      "January–June 2026, after exclusions",
    ) +
    metric(
      fmt(a.sampled - a.usable),
      "Duplicate exclusions",
      `${fmt(a.sampled)} sampled; no invalid required fields`,
    ) +
    metric(
      `${(100 * m.accuracy).toFixed(1)}/100`,
      "Correct routing labels",
      `${fmt(m.correct)}/${fmt(m.test_rows)} locked June test`,
    ) +
    metric(
      pct(m.review, m.test_rows),
      "Sent to review",
      `${fmt(m.review)}/${fmt(m.test_rows)} test narratives`,
    );
  $("brief").innerHTML = data.insights.priorities
    .map(
      (r, i) =>
        `<article class="recommendation" id="${r.evidence_id}"><div class="rank">${i + 1}</div><div><h3>${esc(r.issue)}</h3><p>${esc(r.product)} · Evidence ${r.evidence_id}</p><p><b>Investigate:</b> ${esc(r.recommendation)}</p><p><b>Alternative:</b> ${esc(r.alternative)}</p><p><b>Next check:</b> ${esc(r.next_check)}</p><details><summary>Evidence and intervention hypothesis</summary><p>January–March: ${r.early}/${r.early_denominator}. April–June: ${r.recent}/${r.recent_denominator}. Change ${(r.change_pp >= 0 ? "+" : "") + r.change_pp.toFixed(2)} percentage points. Descriptive month-block interval [${r.change_block_interval.map((v) => v.toFixed(2)).join(", ")}] points, only three months per period.</p><p>${esc(r.hypothesis)}</p><p>${esc(r.evidence_quality)}. Volume ranks the shortlist; a decline can still merit investigation.</p></details></div><div class="evidence-stat"><strong>${fmt(r.n)}</strong>sampled narratives<br>${pct(r.n, r.denominator)} (${fmt(r.n)}/${fmt(r.denominator)})<p>Share change: ${r.change_pp.toFixed(2)} points</p><a href="#trends">Inspect monthly evidence</a></div></article>`,
    )
    .join("");
  $("sensitivity").innerHTML = table(
    ["Signal", "Evidence", "Issue", "Count", "Share change (points)"],
    data.insights.priorities
      .map((r) => [
        "Volume",
        r.evidence_id,
        r.issue,
        fmt(r.n),
        r.change_pp.toFixed(2),
      ])
      .concat(
        data.insights.change_ranking.map((r) => [
          "Change",
          r.evidence_id,
          r.issue,
          fmt(r.n),
          r.change_pp.toFixed(2),
        ]),
      ),
  );
  $("product").innerHTML =
    '<option value="">All products</option>' +
    [...new Set(data.evidence.map((r) => r.product))]
      .sort()
      .map((p) => `<option value="${esc(p)}">${esc(p)}</option>`)
      .join("");
  fillIssues();
  showTrends();
  $("audit").innerHTML = table(
    ["Preparation step", "Records"],
    [
      ["Deterministic monthly sample", fmt(a.sampled)],
      ["Invalid required fields", fmt(a.invalid_required_fields)],
      ["Duplicate identifiers", fmt(a.duplicate_ids)],
      ["Normalized exact duplicates", fmt(a.exact_duplicates)],
      ["Near-duplicates (5-word Jaccard ≥0.85)", fmt(a.near_duplicates)],
      ["Usable after exclusions", fmt(a.usable)],
    ],
  );
  const t = data.timely,
    totalEligible = Object.values(data.manifest.monthly).reduce(
      (s, r) => s + r.eligible,
      0,
    ),
    scanned = data.manifest.archives.reduce((s, r) => s + r.rows, 0);
  $("quality-detail").innerHTML =
    `<p>${fmt(scanned)} archive records scanned; ${fmt(totalEligible)} narratives met the period and minimum-length filter. ${fmt(a.sampled)} selected using the lowest seeded complaint-ID hashes within each month. Archive files remain private.</p><p>Known timely responses: ${pct(t.timely_yes, t.known)} (${fmt(t.timely_yes)}/${fmt(t.known)}); unknown: ${fmt(t.total - t.known)}/${fmt(t.total)}. This does not measure satisfaction or resolution.</p>` +
    table(
      ["Month", "Eligible archive narratives", "Sampled", "Usable"],
      Object.keys(data.manifest.monthly)
        .sort()
        .map((month) => [
          month,
          fmt(data.manifest.monthly[month].eligible),
          fmt(data.manifest.monthly[month].sampled),
          fmt(a.monthly_usable[month]),
        ]),
    ) +
    `<details><summary>Field missingness in the 12,000-row sample</summary>${table(
      ["Field", "Missing", "Denominator"],
      Object.entries(a.missing_fields)
        .filter(([k]) => k !== "month")
        .map(([k, v]) => [k, fmt(v), fmt(a.sampled)]),
    )}</details>`;
  $("model-metrics").innerHTML =
    metric(
      m.macro_f1.toFixed(3),
      "Macro-F1",
      `${m.labels.length} observed product categories`,
    ) +
    metric(
      `${(100 * m.majority.accuracy).toFixed(1)}/100`,
      "Majority baseline",
      `${m.majority.correct}/${m.test_rows} correct`,
    ) +
    metric(
      pct(m.accepted_correct, m.accepted),
      "Accepted-case correctness",
      `${m.accepted_correct}/${m.accepted} accepted test cases`,
    ) +
    metric(
      pct(m.accepted, m.test_rows),
      "Accepted coverage",
      `${m.accepted}/${m.test_rows}; ${m.review} require review`,
    );
  $("model-note").textContent =
    `January–March train (${a.split_counts.train}), April tuning (${a.split_counts.tune}), May threshold selection (${a.split_counts.calibration}), locked June test (${a.split_counts.test}). Threshold ${m.threshold_selection.threshold.toFixed(2)} met ≥90% observed correctness on May; June accepted correctness is ${pct(m.accepted_correct, m.accepted)}, so the calibration target is not a guarantee. Confidence is a raw model score, not a calibrated probability. ${m.test_unseen_rows} unseen-category test records.`;
  $("class-table").innerHTML = table(
    ["Code", "Observed category", "Support", "Precision", "Recall", "F1"],
    m.labels.map((label, i) => {
      const r = m.per_class[label];
      return [
        String.fromCharCode(65 + i),
        label,
        r.support,
        r.precision.toFixed(3),
        r.recall.toFixed(3),
        r["f1-score"].toFixed(3),
      ];
    }),
  );
  $("confusion").innerHTML = table(
    [
      "Observed / predicted",
      ...m.labels.map((_, i) => String.fromCharCode(65 + i)),
    ],
    m.confusion.map((row, i) => [String.fromCharCode(65 + i), ...row]),
  );
  $("monthly-model").innerHTML = table(
    ["Month", "Partition", "Correct / total", "Correctness", "Macro-F1"],
    m.monthly.map((r) => [
      r.month,
      r.split === "train" ? "Train (in-sample)" : r.split,
      `${r.correct}/${r.n}`,
      pct(r.correct, r.n),
      r.macro_f1.toFixed(3),
    ]),
  );
  $("queue-note").textContent =
    `${fmt(data.queue_total)} June cases require review. Lowest-confidence 100 exported; showing up to 8 per view. No human adjudication is claimed.`;
  $("provenance").textContent =
    `Acquired ${data.manifest.acquired_utc.slice(0, 10)} UTC from five official FOIA archives. Seed 42. Private sample SHA-256 ${data.manifest.sample_sha256.slice(0, 16)}… Full hashes and reconciliation are in the repository.`;
  showExample();
  showQueue();
  $("product").addEventListener("change", () => {
    fillIssues();
    showTrends();
  });
  $("issue").addEventListener("change", showTrends);
  $("reset").addEventListener("click", () => {
    $("product").value = "";
    fillIssues();
    showTrends();
  });
  $("example").addEventListener("change", showExample);
  $("queue-filter").addEventListener("change", showQueue);
  $("predict").addEventListener("click", () => {
    const result = infer(model, examples[$("example").value]);
    $("prediction").textContent =
      `${result.category}. Model score ${result.confidence.toFixed(3)}. ${result.review ? "Human review required." : "Above the review threshold; correctness is not guaranteed."}`;
  });
  $("status").hidden = true;
  $("content").hidden = false;
}
Promise.all([
  fetch("data.json").then((r) => {
    if (!r.ok) throw Error("Data unavailable");
    return r.json();
  }),
  fetch("model.json").then((r) => {
    if (!r.ok) throw Error("Model unavailable");
    return r.json();
  }),
])
  .then(([d, m]) => {
    data = d;
    model = m;
    render();
  })
  .catch(() => {
    $("status").textContent =
      "The snapshot could not load. Reload the page, or inspect the downloadable reports in the repository.";
  });
