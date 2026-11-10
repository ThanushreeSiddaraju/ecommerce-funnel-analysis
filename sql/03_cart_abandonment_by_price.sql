-- Cart abandonment = sessions that added to cart but never purchased.
-- Split by the price of the carted item.
SELECT
    CASE
        WHEN cart_price < 100  THEN '1. Under $100'
        WHEN cart_price < 300  THEN '2. $100-299'
        WHEN cart_price < 800  THEN '3. $300-799'
        ELSE                        '4. $800+'
    END                                                                     AS price_band,
    COUNT(*)                                                                AS carted_sessions,
    SUM(reached_purchase = 0)                                               AS abandoned,
    ROUND(100.0 * SUM(reached_purchase = 0) / COUNT(*), 2)                  AS abandonment_pct,
    SUM(removed_from_cart AND reached_purchase = 0)                         AS explicitly_removed
FROM session_flags
WHERE reached_cart = 1
GROUP BY price_band
ORDER BY price_band;
