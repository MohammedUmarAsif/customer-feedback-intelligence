-- Safe aggregate routing evidence. No case identifiers or text are exported.
SELECT month, split, observed, predicted, accepted, COUNT(*)::INTEGER AS n
FROM routing_evaluation
GROUP BY month, split, observed, predicted, accepted
ORDER BY month, observed, predicted, accepted;
