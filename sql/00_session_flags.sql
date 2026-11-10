-- One row per session with a flag for each funnel step it reached.
-- Every other query builds on this view.
DROP VIEW IF EXISTS session_flags;
CREATE VIEW session_flags AS
SELECT
    user_session,
    MIN(user_id)                                                     AS user_id,
    MIN(event_time)                                                  AS session_start,
    -- the category the session browsed most (first viewed is a fine proxy here)
    MIN(CASE WHEN event_type = 'view' THEN category_code END)        AS category_code,
    COUNT(CASE WHEN event_type = 'view' THEN 1 END)                  AS n_views,
    MAX(event_type = 'view')                                         AS reached_view,
    (COUNT(DISTINCT CASE WHEN event_type = 'view' THEN product_id END) >= 2) AS reached_engaged,
    MAX(event_type = 'cart')                                         AS reached_cart,
    MAX(event_type = 'purchase')                                     AS reached_purchase,
    MAX(event_type = 'remove_from_cart')                             AS removed_from_cart,
    MAX(CASE WHEN event_type = 'cart' THEN price END)                AS cart_price
FROM events
GROUP BY user_session;
