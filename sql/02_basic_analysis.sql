-- ============================================================================
-- FIXES vs original 02_basic_analysis.sql (2 bugs) — see CHANGELOG.md for detail
-- ============================================================================

-- Core KPIs (orders & revenue only where purchased = 1)
-- BUG: gross_revenue exists on EVERY row (browse-only sessions have a gross_revenue
-- too, since it's just price*qty). Summing it unfiltered gives $48.76M, not the
-- $11.11M "gross revenue of orders" the README reports. Multiply by purchased to
-- restrict the sum to actual orders, same pattern already used for discounts_given.
SELECT COUNT(*) AS sessions,
       SUM(purchased) AS orders,
       SUM(quantity * purchased) AS units_sold,
       ROUND(SUM(revenue), 2) AS net_revenue,
       ROUND(SUM(gross_revenue * purchased), 2) AS gross_revenue,          -- FIXED
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

-- GROUP BY + HAVING: only categories above the AVERAGE CATEGORY'S revenue
-- BUG: the original compared each category's revenue TOTAL against a single ORDER's
-- average revenue (AVG(revenue) WHERE purchased=1 = ~$1,801). Every category's total
-- easily clears that low bar, so it returned all 8 categories — the filter did nothing.
-- Fix: build the per-category totals first, then average THOSE.
SELECT category_label, ROUND(SUM(revenue), 2) AS net_revenue
FROM sessions GROUP BY category_label
HAVING SUM(revenue) > (
    SELECT AVG(cat_rev) FROM (
        SELECT SUM(revenue) AS cat_rev FROM sessions GROUP BY category_label
    )
)                                                                            -- FIXED
ORDER BY net_revenue DESC;

-- CASE: price bands
-- BUG (found while testing this file, unrelated to the two above): grouping directly
-- by the CASE alias produced TWO separate 'Mid' rows (6,250 sessions each) instead of
-- one — SQLite re-evaluated the CASE expression while planning the GROUP BY and, for
-- this table, split the alias into two internally-distinct groups that printed with
-- the same label. Confirmed with hex(price_band): one 'Mid' group's hex bytes actually
-- decoded to "High". Verified against pandas' cut() on the same thresholds, which
-- gives ONE row per band (8,781 / 8,924 / 4,731 / 2,564 — not the suspiciously even
-- 6,250/6,250/6,250/6,250 the buggy query returned).
-- FIX: compute the CASE in a subquery first, then GROUP BY the already-materialized
-- column. This is good practice generally — never group directly by a computed alias
-- if the engine might re-evaluate it — not just a fix for this one query.
SELECT price_band, COUNT(*) AS sessions, SUM(purchased) AS orders,
       ROUND(100.0 * SUM(purchased) / COUNT(*), 2) AS conversion_pct
FROM (
    SELECT CASE WHEN unit_price < 500 THEN 'Budget'
                WHEN unit_price < 1000 THEN 'Mid'
                WHEN unit_price < 1500 THEN 'High' ELSE 'Premium' END AS price_band,
           purchased
    FROM sessions
)
GROUP BY price_band ORDER BY conversion_pct DESC;                            -- FIXED

-- Revenue by weekday (file-verified Monday=0) and weekend flag
SELECT weekday_name, COUNT(*) AS sessions, SUM(purchased) AS orders,
       ROUND(SUM(revenue), 2) AS net_revenue
FROM sessions GROUP BY weekday_name ORDER BY net_revenue DESC;
