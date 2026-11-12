-- Which brands get carted but not bought? Brands with the most abandoned carts
-- are the first candidates for cart-reminder emails and price checks.
WITH carted AS (
    SELECT DISTINCT user_session, brand, product_id
    FROM events
    WHERE event_type = 'cart' AND brand IS NOT NULL
),
bought AS (
    SELECT DISTINCT user_session, product_id
    FROM events
    WHERE event_type = 'purchase'
)
SELECT
    c.brand,
    COUNT(*)                                                    AS carted_items,
    SUM(b.product_id IS NULL)                                   AS abandoned_items,
    ROUND(100.0 * SUM(b.product_id IS NULL) / COUNT(*), 2)      AS abandonment_pct
FROM carted c
LEFT JOIN bought b
       ON b.user_session = c.user_session AND b.product_id = c.product_id
GROUP BY c.brand
HAVING COUNT(*) >= 20          -- skip brands with too few carts to judge
ORDER BY abandoned_items DESC
LIMIT 15;
