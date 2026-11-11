-- When do shoppers convert? Session funnel by hour of day the session started.
-- Useful for timing campaigns, push notifications and cart-reminder emails.
SELECT
    CAST(SUBSTR(session_start, 12, 2) AS INTEGER)                           AS hour_of_day,
    COUNT(*)                                                                AS sessions,
    ROUND(100.0 * SUM(reached_cart) / COUNT(*), 2)                          AS cart_rate_pct,
    ROUND(100.0 * SUM(reached_purchase) / COUNT(*), 2)                      AS purchase_rate_pct,
    ROUND(100.0 * SUM(reached_purchase) / NULLIF(SUM(reached_cart), 0), 2)  AS cart_to_purchase_pct
FROM session_flags
GROUP BY hour_of_day
ORDER BY hour_of_day;
