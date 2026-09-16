-- Schema & first look
SELECT * FROM sessions LIMIT 10;
PRAGMA table_info(sessions);

-- Grain check: is session_id a primary key?
SELECT COUNT(*) AS rows_total, COUNT(DISTINCT session_id) AS unique_sessions FROM sessions;

-- Cardinality of every dimension
SELECT COUNT(DISTINCT customer_id) AS customers, COUNT(DISTINCT product_id) AS products,
       COUNT(DISTINCT product_category) AS categories, COUNT(DISTINCT location) AS locations,
       COUNT(DISTINCT marketing_channel) AS channels, COUNT(DISTINCT payment_method) AS payments,
       COUNT(DISTINCT device_type) AS devices
FROM sessions;

-- Date coverage
SELECT MIN(visit_date) AS first_visit, MAX(visit_date) AS last_visit,
       julianday(MAX(visit_date)) - julianday(MIN(visit_date)) + 1 AS days_covered
FROM sessions;

-- Duplicate detection (should return 0 rows)
SELECT session_id, COUNT(*) c FROM sessions GROUP BY session_id HAVING c > 1;
SELECT customer_id, visit_date, product_id, COUNT(*) c
FROM sessions GROUP BY 1,2,3 HAVING c > 1;

-- Quick distribution snapshots
SELECT purchased, COUNT(*) AS sessions FROM sessions GROUP BY purchased;
SELECT funnel_stage, COUNT(*) AS sessions FROM sessions GROUP BY funnel_stage;
SELECT discount_percent, COUNT(*) AS sessions FROM sessions GROUP BY discount_percent ORDER BY discount_percent;

