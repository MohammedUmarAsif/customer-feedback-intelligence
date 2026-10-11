-- All counts describe the deduplicated monthly narrative sample, not population failure rates.
SELECT month, product, issue, COUNT(*)::INTEGER AS n
FROM complaints GROUP BY month, product, issue ORDER BY month, product, issue;
