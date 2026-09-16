-- Scalar subquery: products earning above the average per-product revenue
SELECT product_id, ROUND(SUM(revenue), 2) AS net_revenue
FROM sessions WHERE purchased = 1
GROUP BY product_id
HAVING SUM(revenue) > (SELECT AVG(pr) FROM
        (SELECT SUM(revenue) AS pr FROM sessions WHERE purchased = 1 GROUP BY product_id))
ORDER BY net_revenue DESC;

-- Correlated subquery: sessions priced above their own category's average
SELECT s.session_id, s.product_id, s.category_label, s.unit_price,
       (SELECT ROUND(AVG(unit_price), 2) FROM sessions s2
        WHERE s2.product_category = s.product_category) AS category_avg_price
FROM sessions s
WHERE s.unit_price > (SELECT AVG(unit_price) FROM sessions s3
                      WHERE s3.product_category = s.product_category)
LIMIT 15;

-- EXISTS: customers with 2+ purchases
SELECT customer_id, COUNT(*) AS total_sessions, SUM(purchased) AS purchases
FROM sessions s
WHERE EXISTS (SELECT 1 FROM sessions x
              WHERE x.customer_id = s.customer_id AND x.purchased = 1)
GROUP BY customer_id HAVING SUM(purchased) >= 2;

-- Derived-table join (stand-in for a fact→dim join in a star schema)
SELECT p.product_id, p.net_revenue, c.category_orders,
       ROUND(100.0 * p.net_revenue / c.category_revenue, 2) AS share_of_category_pct
FROM (SELECT product_id, category_label, SUM(revenue) AS net_revenue
      FROM sessions WHERE purchased = 1 GROUP BY product_id) p
JOIN (SELECT category_label,
             SUM(revenue) AS category_revenue,
             SUM(purchased) AS category_orders
      FROM sessions GROUP BY category_label) c
  ON p.category_label = c.category_label
ORDER BY share_of_category_pct DESC LIMIT 15;
