-- Monthly aggregation with conversion
SELECT strftime('%Y-%m', visit_date) AS ym,
       COUNT(*) AS sessions, SUM(purchased) AS orders,
       ROUND(100.0 * AVG(purchased), 2) AS conversion_pct,
       ROUND(SUM(revenue), 2) AS net_revenue
FROM sessions GROUP BY ym ORDER BY ym;

-- Previous-period comparison per month
WITH m AS (SELECT strftime('%Y-%m', visit_date) AS ym, SUM(revenue) AS rev FROM sessions GROUP BY ym)
SELECT ym, ROUND(rev, 2) AS revenue,
       LAG(ROUND(rev, 2)) OVER (ORDER BY ym) AS prev_month_revenue,
       ROUND(rev - LAG(rev) OVER (ORDER BY ym), 2) AS change_abs
FROM m ORDER BY ym;

-- Calendar-spanning daily series (zero-fills missing days) via recursive CTE
WITH RECURSIVE cal(d) AS (
    SELECT (SELECT MIN(visit_date) FROM sessions)
    UNION ALL
    SELECT date(d, '+1 day') FROM cal
    WHERE d < (SELECT MAX(visit_date) FROM sessions)
)
SELECT cal.d AS day,
       COUNT(s.session_id) AS sessions,
       COALESCE(SUM(s.revenue), 0) AS revenue
FROM cal LEFT JOIN sessions s ON s.visit_date = cal.d
GROUP BY cal.d ORDER BY cal.d;

-- 7-day rolling average on that series
WITH RECURSIVE cal(d) AS (
    SELECT (SELECT MIN(visit_date) FROM sessions)
    UNION ALL SELECT date(d, '+1 day') FROM cal
    WHERE d < (SELECT MAX(visit_date) FROM sessions)
),
daily AS (
    SELECT cal.d AS day, COALESCE(SUM(s.revenue), 0) AS rev
    FROM cal LEFT JOIN sessions s ON s.visit_date = cal.d GROUP BY cal.d
)
SELECT day, ROUND(rev, 2) AS revenue,
       ROUND(AVG(rev) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS ma_7d
FROM daily ORDER BY day;

-- Season & weekday patterns (encodings verified in validation)
SELECT season_name, COUNT(*) AS sessions, SUM(purchased) AS orders,
       ROUND(SUM(revenue), 2) AS net_revenue,
       ROUND(100.0 * AVG(purchased), 2) AS conversion_pct
FROM sessions GROUP BY season_name ORDER BY net_revenue DESC;

SELECT visit_weekday, weekday_name, COUNT(*) AS sessions,
       ROUND(SUM(revenue), 2) AS net_revenue,
       ROUND(AVG(revenue), 2) AS avg_order_value
FROM sessions WHERE purchased = 1
GROUP BY visit_weekday, weekday_name ORDER BY visit_weekday;
