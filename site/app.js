"use strict";
let data,
  model,
  queuePage = 0;
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
function plainFinding(row) {
  const explanations = {
    "Debt collection|Attempts to collect debt not owed": [
      "Asked to repay money they say they do not owe",
      "Did the team check who owed the money before asking for payment?",
    ],
    "Checking or savings account|Managing an account": [
      "Problems managing a bank account",
      "Where do customers get stuck when accessing or managing their account?",
    ],
    "Credit card|Problem with a purchase shown on your statement": [
      "Problems with purchases on a card bill",
      "Is it clear how to question a purchase and what evidence to provide?",
    ],
  };
  return (
    explanations[`${row.product}|${row.issue}`] || [
      row.issue,
      row.recommendation,
    ]
  );
}
function showExample() {
  document
    .querySelectorAll("[data-example]")
    .forEach((button) =>
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.example === $("example").value),
      ),
    );
  $("recognized-words").textContent = "";
  $("example-text").textContent = examples[$("example").value];
  $("prediction").textContent = model
    ? "Select Suggest a category to see the model output."
    : "Loading the example model…";
}
function showQueue() {
  const matching = data.queue.filter(
    (r) => $("queue-filter").value !== "errors" || r.observed !== r.predicted,
  );
  const rows = matching.slice(queuePage * 8, (queuePage + 1) * 8);
  $("queue-page").textContent = matching.length
    ? `${queuePage * 8 + 1} to ${Math.min((queuePage + 1) * 8, matching.length)} of ${matching.length} preview cases`
    : "No matching preview cases";
  $("queue-prev").disabled = queuePage === 0;
  $("queue-next").disabled = (queuePage + 1) * 8 >= matching.length;
  $("queue").innerHTML = rows.length
    ? table(
        ["Case", "Published category", "Model suggestion", "Model score"],
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
function drawTrend(traces, months) {
  // A responsive SVG is sufficient for six monthly points; no chart runtime needed.
  const width = 640,
    height = 280,
    left = 60,
    right = 20,
    top = 25,
    bottom = 40;
  const max = Math.max(
    5,
    Math.ceil(
      Math.max(...traces.flatMap((t) => t.y).filter((v) => v !== null), 0) / 5,
    ) * 5,
  );
  const x = (i) => left + (i * (width - left - right)) / (months.length - 1);
  const y = (value) =>
    height - bottom - (value / max) * (height - top - bottom);
  let svg = `<svg class="trend-svg" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="trend-title trend-desc"><title id="trend-title">Monthly share of sampled complaints</title><desc id="trend-desc">${esc(traces.map((t) => t.name).join("; "))}. Percentages use each month's selected product sample. Exact values are in the monthly evidence table below.</desc>`;
  for (let i = 0; i <= 4; i++) {
    const value = (max * i) / 4;
    svg += `<line x1="${left}" y1="${y(value)}" x2="${width - right}" y2="${y(value)}" stroke="#d5e0e1"/><text x="${left - 8}" y="${y(value) + 5}" text-anchor="end" font-size="14" fill="#4b626a">${Number(value.toFixed(1))}%</text>`;
  }
  months.forEach((month, i) => {
    svg += `<text x="${x(i)}" y="${height - 12}" text-anchor="middle" font-size="14" fill="#4b626a">${["Jan", "Feb", "Mar", "Apr", "May", "Jun"][Number(month.slice(5)) - 1]}</text>`;
  });
  traces.forEach((trace, k) => {
    let path = "",
      penDown = false;
    trace.y.forEach((value, i) => {
      if (value === null) {
        penDown = false;
        return;
      }
      path += `${penDown ? "L" : "M"}${x(i)},${y(value)} `;
      penDown = true;
    });
    svg += `<path d="${path}" fill="none" stroke="${trace.line.color}" stroke-width="3" stroke-dasharray="${["none", "8 4", "2 4"][k]}"/>`;
    trace.y.forEach((value, i) => {
      if (value !== null)
        svg += `<circle cx="${x(i)}" cy="${y(value)}" r="4" fill="${trace.line.color}"><title>${esc(trace.name)} · ${months[i]}: ${value.toFixed(1)}% (${trace.customdata[i][0]}/${trace.customdata[i][1]})</title></circle>`;
    });
  });
  $("trend-chart").innerHTML = traces.length
    ? svg + "</svg>"
    : "<p>No complaints match these filters.</p>";
  $("trend-legend").innerHTML = traces
    .map(
      (trace, k) =>
        `<span><span class="legend-line" style="border-color:${trace.line.color};border-top-style:${["solid", "dashed", "dotted"][k]}" aria-hidden="true"></span>${esc(trace.name)}</span>`,
    )
    .join("");
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
    `${product || "All products"} · ${fmt(denom)} sampled complaints, January to June 2026. ${issue ? `Selected issue: ${issue}. Chart shares use this product’s monthly complaint sample. The bars above use all 10,950 complaints.` : "Lines show the three most frequent issues. Percentages use the selected product’s monthly sample."}`;
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
  drawTrend(traces, months);
  $("trend-table").innerHTML = table(
    ["Month", "Issue", "Count", "Monthly denominator", "Share"],
    monthRows,
  );
  $("issue-table").innerHTML = table(
    ["Recurring issue", "Count", "Share of selected sample"],
    (issue ? [issue] : ranked)
      .slice(0, 10)
      .map((i) => [
        i,
        fmt(counts[i]),
        `${pct(counts[i], denom)} (${fmt(counts[i])}/${fmt(denom)})`,
      ]),
  );
}
function selectPriority(index) {
  const priority = data.insights.priorities[index];
  $("product").value = priority.product;
  fillIssues();
  $("issue").value = priority.issue;
  $("finding-question").textContent = plainFinding(priority)[1];
  document
    .querySelectorAll("[data-priority]")
    .forEach((link) =>
      link.setAttribute(
        "aria-current",
        String(Number(link.dataset.priority) === index),
      ),
    );
  showTrends();
}
function predictExample() {
  if (!model) return;
  const result = infer(model, examples[$("example").value]);
  const recognized = [
    ...new Set(examples[$("example").value].toLowerCase().match(/[a-z]{2,}/g)),
  ].filter((word) => Object.hasOwn(model.vocabulary, word));
  $("recognized-words").textContent =
    `Recognised words: ${recognized.join(", ") || "none"}. Model score: ${result.confidence.toFixed(3)}; review cutoff: ${data.metrics.threshold_selection.threshold.toFixed(2)}.`;
  $("prediction").textContent =
    `${result.review ? "Human review flagged." : "Above the review cutoff."} Suggested category: ${result.category}.${$("example").value === "credit" ? " This is a mistake: the message describes a credit report error." : ""}`;
}
function render() {
  const a = data.audit,
    m = data.metrics;
  const priorities = data.insights.priorities;
  const largest = Math.max(...priorities.map((r) => r.n));
  $("brief").innerHTML = priorities
    .map(
      (r, i) =>
        `<a class="finding-link finding-row recommendation" data-priority="${i}" href="#trends" aria-current="${i === 0 ? "true" : "false"}"><span class="finding-label">${esc(plainFinding(r)[0])}</span><span class="finding-track" aria-hidden="true"><span style="width:${(100 * r.n) / largest}%"></span></span><span class="finding-count">${fmt(r.n)}<small>${pct(r.n, r.denominator)} of sample</small></span></a>`,
    )
    .join("");
  $("finding-research").innerHTML = priorities
    .map(
      (r) =>
        `<article><h3>${esc(plainFinding(r)[0])}</h3><p><b>Recorded issue:</b> ${esc(r.issue)} (${esc(r.product)}).</p><p><b>Investigation:</b> ${esc(r.next_check)}</p><p><b>Alternative explanation:</b> ${esc(r.alternative)}</p><p><b>Testable hypothesis:</b> ${esc(r.hypothesis)}</p><p>Evidence ${esc(r.evidence_id)}: ${fmt(r.n)} / ${fmt(r.denominator)} sampled complaints. January to March: ${r.early}/${r.early_denominator}; April to June: ${r.recent}/${r.recent_denominator}. Share change: ${r.change_pp.toFixed(2)} percentage points. Descriptive month-block interval: ${r.change_block_interval.map((v) => v.toFixed(2)).join(" to ")} points. Only three months per period; this does not prove a trend or cause.</p></article>`,
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
  selectPriority(0);
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
      pct(m.correct, m.test_rows),
      "Matched the published category",
      `${fmt(m.correct)} of ${fmt(m.test_rows)} June complaints`,
    ) +
    metric(
      pct(m.review, m.test_rows),
      "Flagged for human review",
      `${fmt(m.review)} of ${fmt(m.test_rows)} June complaints`,
    ) +
    metric(
      pct(m.accepted_correct, m.accepted),
      "Accuracy above the score cutoff",
      `${m.accepted_correct}/${m.accepted} higher-score cases only`,
    ) +
    metric(
      pct(m.accepted, m.test_rows),
      "Cases above the score cutoff",
      `${m.accepted}/${m.test_rows}; the other ${m.review} need review`,
    );
  const acceptedDots = Math.round((100 * m.accepted) / m.test_rows);
  const correctDots = Math.round((100 * m.accepted_correct) / m.test_rows);
  const wrongDots = acceptedDots - correctDots;
  const reviewDots = 100 - acceptedDots;
  $("routing-summary").textContent =
    "About half the messages were flagged for review. Among suggestions above the cutoff, about 90% matched the published category.";
  $("reliability-dots").innerHTML = Array.from(
    { length: 100 },
    (_, i) =>
      `<span class="dot ${i < correctDots ? "correct" : i < acceptedDots ? "incorrect" : "review"}" aria-hidden="true"></span>`,
  ).join("");
  $("reliability-dots").setAttribute(
    "aria-label",
    `Rounded June results per 100 messages: ${correctDots} above-cutoff correct suggestions, ${wrongDots} above-cutoff incorrect suggestions, ${reviewDots} flagged for review.`,
  );
  $("reliability-legend").innerHTML =
    [
      ["correct", correctDots, "Above cutoff, correct"],
      ["incorrect", wrongDots, "Above cutoff, incorrect"],
      ["review", reviewDots, "Flagged for a person"],
    ]
      .map(
        ([cls, n, label]) =>
          `<div><span class="dot ${cls}" aria-hidden="true"></span><strong>${n}</strong><span>${label}</span></div>`,
      )
      .join("") +
    `<small>Exact test counts: ${m.accepted_correct} correct and ${m.accepted - m.accepted_correct} incorrect above cutoff; ${m.review} flagged.</small>`;
  $("accuracy-comparison").innerHTML = [
    ["Always choose the most common category", m.majority.accuracy, "baseline"],
    ["Read the text with the trained model", m.accuracy, ""],
  ]
    .map(
      ([label, accuracy, cls]) =>
        `<div class="bar-label"><span>${label}</span><strong>${(accuracy * 100).toFixed(1)}%</strong></div><div class="bar-track" aria-hidden="true"><div class="bar-fill ${cls}" style="width:${accuracy * 100}%"></div></div>`,
    )
    .join("");
  $("accuracy-gain").textContent =
    `${((m.accuracy - m.majority.accuracy) * 100).toFixed(1)} percentage points higher accuracy on this test. This measures category matching, not service outcomes.`;
  $("technical-metrics").textContent =
    `Macro-F1: ${m.macro_f1.toFixed(3)} (balances performance across the ${m.labels.length} categories; higher is better). Majority baseline: ${pct(m.majority.correct, m.test_rows)} (${m.majority.correct}/${m.test_rows}), obtained by always choosing the most common training category. Rare-category results remain weak; see recall below.`;
  $("model-note").textContent =
    `January to March train (${a.split_counts.train}), April tuning (${a.split_counts.tune}), May threshold selection (${a.split_counts.calibration}), locked June test (${a.split_counts.test}). Threshold ${m.threshold_selection.threshold.toFixed(2)} met ≥90% observed correctness on May; June accepted correctness is ${pct(m.accepted_correct, m.accepted)}, so the calibration target is not a guarantee. Confidence is a raw model score, not a calibrated probability. ${m.test_unseen_rows} unseen-category test records.`;
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
    `${fmt(data.queue_total)} June cases were flagged. This preview contains the 100 lowest-score cases, eight per page. The model score is not a probability of being correct. These cases have not been adjudicated by a person.`;
  $("provenance").textContent =
    `Acquired ${data.manifest.acquired_utc.slice(0, 10)} UTC from five official FOIA archives. Seed 42. Private sample SHA-256 ${data.manifest.sample_sha256.slice(0, 16)}… Full hashes and reconciliation are in the repository.`;
  showExample();
  showQueue();
  document.querySelectorAll("[data-priority]").forEach((link) => {
    link.addEventListener("click", () => {
      selectPriority(Number(link.dataset.priority));
      $("evidence-heading").focus({ preventScroll: true });
    });
  });
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
  $("example").addEventListener("change", () => {
    showExample();
    if (model) predictExample();
  });
  document.querySelectorAll("[data-example]").forEach((button) => {
    button.disabled = !model;
    button.addEventListener("click", () => {
      $("example").value = button.dataset.example;
      showExample();
      predictExample();
    });
  });
  $("queue-filter").addEventListener("change", () => {
    queuePage = 0;
    showQueue();
  });
  $("queue-prev").addEventListener("click", () => {
    queuePage--;
    showQueue();
  });
  $("queue-next").addEventListener("click", () => {
    queuePage++;
    showQueue();
  });
  $("predict").addEventListener("click", predictExample);
  $("status").hidden = true;
  $("content").hidden = false;
  document.querySelectorAll(".table-wrap").forEach((region) => {
    region.tabIndex = 0;
    region.setAttribute("role", "region");
    region.setAttribute(
      "aria-label",
      (region.querySelector("th")?.textContent || "Evidence") +
        " table; scroll horizontally if needed",
    );
  });
}
Promise.allSettled([
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
    if (d.status !== "fulfilled") throw Error("Data unavailable");
    data = d.value;
    model = m.status === "fulfilled" ? m.value : null;
    render();
    $("predict").disabled = !model;
    if (!model)
      $("prediction").textContent =
        "The example model could not load. You can still explore the findings and measured results. Reload to try the model again.";
  })
  .catch(() => {
    $("content").hidden = true;
    $("status").hidden = false;
    $("status").innerHTML =
      'The snapshot could not load. <button type="button" id="retry">Try again</button> or <a href="https://github.com/MohammedUmarAsif/customer-feedback-intelligence/blob/main/docs/decision_brief.md">read the findings on GitHub</a>.';
    $("retry").addEventListener("click", () => location.reload());
  });

const chapters = ["priorities", "routing", "reliability", "method"];
const chapterObserver = new IntersectionObserver(
  (entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
    if (!visible) return;
    document.querySelectorAll("nav a").forEach((link) => {
      if (link.hash === `#${visible.target.id}`)
        link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  },
  { rootMargin: "-15% 0px -55% 0px" },
);
chapters.forEach((id) => chapterObserver.observe($(id)));
