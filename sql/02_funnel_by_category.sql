-- Same funnel split by product category: where is each category leaking?
SELECT
    category_code,
    SUM(reached_view)                                                       AS viewed,
    SUM(reached_cart)                                                       AS carted,
    SUM(reached_purchase)                                                   AS purchased,
    ROUND(100.0 * SUM(reached_cart)     / SUM(reached_view), 2)             AS view_to_cart_pct,
    ROUND(100.0 * SUM(reached_purchase) / NULLIF(SUM(reached_cart), 0), 2)  AS cart_to_purchase_pct,
    ROUND(100.0 * SUM(reached_purchase) / SUM(reached_view), 2)             AS overall_conversion_pct
FROM session_flags
WHERE category_code IS NOT NULL
GROUP BY category_code
ORDER BY overall_conversion_pct DESC;
