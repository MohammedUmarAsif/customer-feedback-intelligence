/* Exact exported sklearn sublinear TF-IDF, L2 normalization, multinomial softmax. */
function infer(model, text) {
  const words = text.toLowerCase().match(/[a-z]{2,}/g) || [],
    counts = {};
  for (const word of words) {
    const i = model.vocabulary[word];
    if (i !== undefined) counts[i] = (counts[i] || 0) + 1;
  }
  const x = Array(model.idf.length).fill(0);
  let norm = 0;
  for (const [i, count] of Object.entries(counts)) {
    x[i] = (1 + Math.log(count)) * model.idf[i];
    norm += x[i] * x[i];
  }
  norm = Math.sqrt(norm);
  if (norm) x.forEach((v, i) => (x[i] = v / norm));
  const scores = model.coefficients.map((row, k) =>
    row.reduce((s, w, i) => s + w * x[i], model.intercept[k]),
  );
  const max = Math.max(...scores),
    exp = scores.map((s) => Math.exp(s - max)),
    sum = exp.reduce((a, b) => a + b, 0),
    prob = exp.map((v) => v / sum);
  const k = prob.indexOf(Math.max(...prob));
  return {
    category: model.classes[k],
    confidence: prob[k],
    review: prob[k] < model.threshold,
    probabilities: prob,
  };
}
if (typeof module !== "undefined") module.exports = { infer };
