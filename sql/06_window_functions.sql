-- RANK: top 3 products per category
WITH prod AS (
    SELECT category_label, product_id, SUM(revenue) AS net_revenue
    FROM sessions WHERE purchased = 1 GROUP BY category_label, product_id
),
ranked AS (
    SELECT *, RANK() OVER (PARTITION BY category_label ORDER BY net_revenue DESC) AS rnk
    FROM prod
)
SELECT category_label, product_id, ROUND(net_revenue, 2) AS net_revenue, rnk
FROM ranked WHERE rnk <= 3 ORDER BY category_label, rnk;

-- DENSE_RANK: customer revenue tiers
WITH cv AS (SELECT customer_id, SUM(revenue) AS ltv FROM sessions WHERE purchased = 1 GROUP BY customer_id)
SELECT customer_id, ROUND(ltv, 2) AS lifetime_value,
       DENSE_RANK() OVER (ORDER BY ltv DESC) AS revenue_rank
FROM cv ORDER BY revenue_rank LIMIT 20;

-- ROW_NUMBER: latest purchase per customer
WITH seq AS (
    SELECT customer_id, session_id, visit_date, revenue,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY visit_date DESC, session_id DESC) AS rn
    FROM sessions WHERE purchased = 1
)
SELECT customer_id, session_id, visit_date, ROUND(revenue, 2) AS latest_order_value
FROM seq WHERE rn = 1;

-- LAG: month-over-month growth
WITH m AS (SELECT strftime('%Y-%m', visit_date) AS ym, SUM(revenue) AS rev FROM sessions GROUP BY ym)
SELECT ym, ROUND(rev, 2) AS revenue,
       ROUND(LAG(rev) OVER (ORDER BY ym), 2) AS prev_month,
       ROUND(100.0 * (rev - LAG(rev) OVER (ORDER BY ym))
             / NULLIF(LAG(rev) OVER (ORDER BY ym), 0), 2) AS growth_pct
FROM m ORDER BY ym;

-- LEAD: gap between a customer's consecutive purchases
WITH ordered AS (
    SELECT customer_id, visit_date,
           LEAD(visit_date) OVER (PARTITION BY customer_id ORDER BY visit_date) AS next_visit
    FROM sessions WHERE purchased = 1
)
SELECT customer_id, visit_date, next_visit,
       CAST(julianday(next_visit) - julianday(visit_date) AS INT) AS days_between
FROM ordered WHERE next_visit IS NOT NULL ORDER BY days_between DESC LIMIT 15;

-- Running total & moving average of daily revenue
WITH d AS (
    SELECT visit_date AS day, SUM(revenue) AS rev
    FROM sessions WHERE purchased = 1 GROUP BY visit_date
)
SELECT day, ROUND(rev, 2) AS revenue,
       ROUND(SUM(rev) OVER (ORDER BY day), 2) AS running_total,
       ROUND(AVG(rev) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS ma_7d
FROM d ORDER BY day;

-- SUM() OVER: each category's share of total revenue
SELECT category_label, ROUND(SUM(revenue), 2) AS net_revenue,
       ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS share_pct
FROM sessions WHERE purchased = 1 GROUP BY category_label;
