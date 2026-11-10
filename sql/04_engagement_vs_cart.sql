-- Does browsing depth predict add-to-cart? (views per session vs cart rate)
SELECT
    CASE WHEN n_views >= 6 THEN '6+' ELSE CAST(n_views AS TEXT) END         AS views_in_session,
    COUNT(*)                                                                AS sessions,
    ROUND(100.0 * SUM(reached_cart) / COUNT(*), 2)                          AS cart_rate_pct,
    ROUND(100.0 * SUM(reached_purchase) / COUNT(*), 2)                      AS purchase_rate_pct
FROM session_flags
WHERE n_views > 0
GROUP BY views_in_session
ORDER BY MIN(n_views);
