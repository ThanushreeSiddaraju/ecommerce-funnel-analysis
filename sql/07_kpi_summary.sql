-- Headline KPIs in one row: the numbers a growth team checks first.
SELECT
    (SELECT COUNT(DISTINCT user_id) FROM events)                                    AS users,
    COUNT(*)                                                                        AS sessions,
    ROUND(100.0 * SUM(reached_purchase) / COUNT(*), 2)                              AS session_conversion_pct,
    ROUND(100.0 * SUM(reached_cart AND reached_purchase = 0)
                / NULLIF(SUM(reached_cart), 0), 2)                                  AS cart_abandonment_pct,
    (SELECT ROUND(SUM(price), 2) FROM events WHERE event_type = 'purchase')         AS revenue,
    (SELECT ROUND(AVG(price), 2) FROM events WHERE event_type = 'purchase')         AS avg_order_value
FROM session_flags;
