-- Overall session funnel: how many sessions reach each step,
-- step-to-step conversion, and how many sessions each step loses.
WITH steps AS (
    SELECT 1 AS step_order, '1. Viewed a product'        AS step, SUM(reached_view)     AS sessions FROM session_flags
    UNION ALL
    SELECT 2, '2. Viewed 2+ products (engaged)', SUM(reached_view AND reached_engaged)               FROM session_flags
    UNION ALL
    SELECT 3, '3. Added to cart',                SUM(reached_view AND reached_engaged AND reached_cart) FROM session_flags
    UNION ALL
    SELECT 4, '4. Purchased',                    SUM(reached_view AND reached_engaged AND reached_cart AND reached_purchase) FROM session_flags
)
SELECT
    step,
    sessions,
    ROUND(100.0 * sessions / FIRST_VALUE(sessions) OVER (ORDER BY step_order), 2)          AS pct_of_top,
    ROUND(100.0 * sessions / LAG(sessions) OVER (ORDER BY step_order), 2)                  AS step_conversion_pct,
    LAG(sessions) OVER (ORDER BY step_order) - sessions                                    AS sessions_lost,
    ROUND(100.0 - 100.0 * sessions / LAG(sessions) OVER (ORDER BY step_order), 2)          AS step_dropoff_pct
FROM steps
ORDER BY step_order;
