-- Q1 Which products generate the most revenue?
SELECT product_id, category_label, COUNT(*) AS orders, SUM(quantity) AS units,
       ROUND(SUM(revenue), 2) AS net_revenue
FROM sessions WHERE purchased = 1
GROUP BY product_id, category_label ORDER BY net_revenue DESC LIMIT 15;

-- Q2 What share of revenue does each category contribute?
SELECT category_label, ROUND(SUM(revenue), 2) AS net_revenue,
       ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM sessions WHERE purchased = 1), 2) AS share_pct
FROM sessions WHERE purchased = 1 GROUP BY category_label ORDER BY share_pct DESC;

-- Q3 Which channels convert best, and do they also drive bigger baskets?
SELECT channel_label,
       ROUND(100.0 * AVG(purchased), 2) AS conversion_pct,
       ROUND(AVG(CASE WHEN purchased = 1 THEN revenue END), 2) AS aov
FROM sessions GROUP BY channel_label ORDER BY conversion_pct DESC;

-- Q4 Are deeper discounts associated with higher conversion? (association only)
SELECT discount_percent, COUNT(*) AS sessions, SUM(purchased) AS orders,
       ROUND(100.0 * AVG(purchased), 2) AS conversion_pct,
       ROUND(AVG(CASE WHEN purchased = 1 THEN revenue END), 2) AS aov
FROM sessions GROUP BY discount_percent ORDER BY discount_percent;

-- Q5 Which locations generate the most revenue?
SELECT location, COUNT(*) AS orders, ROUND(SUM(revenue), 2) AS net_revenue
FROM sessions WHERE purchased = 1 GROUP BY location ORDER BY net_revenue DESC LIMIT 15;

-- Q6 Repeat customers: who purchased more than once?
SELECT customer_id, COUNT(*) AS orders, ROUND(SUM(revenue), 2) AS lifetime_revenue
FROM sessions WHERE purchased = 1 GROUP BY customer_id
HAVING COUNT(*) > 1 ORDER BY lifetime_revenue DESC LIMIT 15;

-- Q7 Do engaged sessions convert more? (median-split comparison)
SELECT CASE WHEN time_on_site_sec >= (SELECT AVG(time_on_site_sec) FROM sessions)
            THEN 'above-avg time' ELSE 'below-avg time' END AS engagement,
       COUNT(*) AS sessions, ROUND(100.0 * AVG(purchased), 2) AS conversion_pct
FROM sessions GROUP BY engagement;

-- Q8 Which payment methods appear on purchased sessions?
SELECT payment_label, SUM(purchased) AS orders,
       ROUND(AVG(CASE WHEN purchased = 1 THEN revenue END), 2) AS aov
FROM sessions GROUP BY payment_label ORDER BY orders DESC;
