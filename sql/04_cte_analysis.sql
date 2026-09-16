-- CTE chain 1: full funnel per channel (browse → cart → purchase)
WITH per_channel AS (
    SELECT channel_label,
           COUNT(*) AS sessions,
           SUM(added_to_cart) AS cart_adds,
           SUM(purchased) AS purchases
    FROM sessions GROUP BY channel_label
)
SELECT channel_label, sessions, cart_adds, purchases,
       ROUND(100.0 * cart_adds / sessions, 2) AS cart_rate_pct,
       ROUND(100.0 * purchases / NULLIF(cart_adds, 0), 2) AS cart_to_purchase_pct,
       ROUND(100.0 * purchases / sessions, 2) AS overall_conversion_pct
FROM per_channel ORDER BY overall_conversion_pct DESC;

-- CTE chain 2: monthly revenue + previous month via join
WITH monthly AS (
    SELECT strftime('%Y-%m', visit_date) AS ym, SUM(revenue) AS rev, SUM(purchased) AS orders
    FROM sessions GROUP BY ym
),
lagged AS (
    SELECT ym, rev, orders, LAG(rev) OVER (ORDER BY ym) AS prev_rev
    FROM monthly
)
SELECT ym, ROUND(rev, 2) AS revenue, orders,
       ROUND(prev_rev, 2) AS prev_revenue,
       ROUND(100.0 * (rev - prev_rev) / NULLIF(prev_rev, 0), 2) AS mom_growth_pct
FROM lagged ORDER BY ym;

-- CTE chain 3: customer value tiers joined back to behaviour
WITH cust_value AS (
    SELECT customer_id, SUM(revenue) AS lifetime_value, COUNT(*) AS orders
    FROM sessions WHERE purchased = 1 GROUP BY customer_id
),
tiers AS (
    SELECT customer_id, lifetime_value, orders,
           NTILE(4) OVER (ORDER BY lifetime_value) AS value_quartile
    FROM cust_value
)
SELECT value_quartile, COUNT(*) AS customers, ROUND(AVG(lifetime_value), 2) AS avg_ltv,
       ROUND(AVG(orders), 2) AS avg_orders
FROM tiers GROUP BY value_quartile ORDER BY value_quartile DESC;

