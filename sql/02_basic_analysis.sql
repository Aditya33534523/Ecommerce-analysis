-- Core KPIs (orders & revenue only where purchased = 1)
SELECT COUNT(*) AS sessions,
       SUM(purchased) AS orders,
       SUM(quantity * purchased) AS units_sold,
       ROUND(SUM(revenue), 2) AS net_revenue,
       ROUND(SUM(gross_revenue), 2) AS gross_revenue,
       ROUND(SUM(discount_amount * purchased), 2) AS discounts_given,
       ROUND(AVG(CASE WHEN purchased = 1 THEN revenue END), 2) AS aov,
       ROUND(100.0 * SUM(purchased) / COUNT(*), 2) AS conversion_rate_pct,
       ROUND(100.0 * SUM(CASE WHEN added_to_cart = 1 AND purchased = 0 THEN 1 ELSE 0 END)
             / NULLIF(SUM(added_to_cart), 0), 2) AS cart_abandonment_pct
FROM sessions;

-- Revenue by category
SELECT category_label, SUM(purchased) AS orders, ROUND(SUM(revenue), 2) AS net_revenue
FROM sessions GROUP BY category_label ORDER BY net_revenue DESC;

-- Conversion & AOV by channel
SELECT channel_label, COUNT(*) AS sessions, SUM(purchased) AS orders,
       ROUND(100.0 * AVG(purchased), 2) AS conversion_pct,
       ROUND(AVG(CASE WHEN purchased = 1 THEN revenue END), 2) AS aov
FROM sessions GROUP BY channel_label ORDER BY conversion_pct DESC;

-- GROUP BY + HAVING: only categories above average category revenue
SELECT category_label, ROUND(SUM(revenue), 2) AS net_revenue
FROM sessions GROUP BY category_label
HAVING SUM(revenue) > (SELECT AVG(revenue) FROM sessions WHERE purchased = 1)
ORDER BY net_revenue DESC;

-- CASE: price bands
SELECT CASE WHEN unit_price < 500 THEN 'Budget'
            WHEN unit_price < 1000 THEN 'Mid'
            WHEN unit_price < 1500 THEN 'High' ELSE 'Premium' END AS price_band,
       COUNT(*) AS sessions, SUM(purchased) AS orders,
       ROUND(AVG(purchased) * 100, 2) AS conversion_pct
FROM sessions GROUP BY price_band ORDER BY conversion_pct DESC;

-- Revenue by weekday (file-verified Monday=0) and weekend flag
SELECT weekday_name, COUNT(*) AS sessions, SUM(purchased) AS orders,
       ROUND(SUM(revenue), 2) AS net_revenue
FROM sessions GROUP BY weekday_name ORDER BY net_revenue DESC;
