-- ============================================================
-- sales_db  –  Analytics Queries
-- ============================================================

-- ── 1. Top 10 Customers by Revenue ───────────────────────────
SELECT
    dc.customer_unique_id,
    dc.customer_state,
    COUNT(DISTINCT fs.order_id)        AS total_orders,
    ROUND(SUM(fs.revenue)::NUMERIC, 2) AS total_revenue,
    ROUND(AVG(fs.revenue)::NUMERIC, 2) AS avg_order_value
FROM fact_sales fs
JOIN dim_customer dc ON fs.customer_id = dc.customer_id
GROUP BY dc.customer_unique_id, dc.customer_state
ORDER BY total_revenue DESC
LIMIT 10;


-- ── 2. Monthly Revenue ────────────────────────────────────────
SELECT
    dd.year,
    dd.month,
    dd.month_name,
    COUNT(DISTINCT fs.order_id)        AS total_orders,
    ROUND(SUM(fs.revenue)::NUMERIC, 2) AS monthly_revenue,
    ROUND(SUM(fs.profit)::NUMERIC, 2)  AS monthly_profit
FROM fact_sales fs
JOIN dim_date dd ON fs.date_id = dd.date_id
WHERE fs.order_status = 'delivered'
GROUP BY dd.year, dd.month, dd.month_name
ORDER BY dd.year, dd.month;


-- ── 3. Revenue by State ───────────────────────────────────────
SELECT
    dc.customer_state,
    COUNT(DISTINCT fs.order_id)        AS total_orders,
    ROUND(SUM(fs.revenue)::NUMERIC, 2) AS total_revenue
FROM fact_sales fs
JOIN dim_customer dc ON fs.customer_id = dc.customer_id
WHERE fs.order_status = 'delivered'
GROUP BY dc.customer_state
ORDER BY total_revenue DESC;


-- ── 4. Top 10 Selling Products ────────────────────────────────
SELECT
    dp.product_id,
    dp.product_category_name,
    COUNT(*)                           AS times_ordered,
    ROUND(SUM(fs.revenue)::NUMERIC, 2) AS product_revenue
FROM fact_sales fs
JOIN dim_product dp ON fs.product_id = dp.product_id
GROUP BY dp.product_id, dp.product_category_name
ORDER BY times_ordered DESC
LIMIT 10;


-- ── 5. Average Order Value Overall ───────────────────────────
SELECT
    ROUND(AVG(order_revenue)::NUMERIC, 2) AS avg_order_value
FROM (
    SELECT order_id, SUM(revenue) AS order_revenue
    FROM fact_sales
    GROUP BY order_id
) sub;


-- ── 6. Customer Retention – Repeat Customers ─────────────────
WITH customer_orders AS (
    SELECT
        dc.customer_unique_id,
        COUNT(DISTINCT fs.order_id) AS order_count
    FROM fact_sales fs
    JOIN dim_customer dc ON fs.customer_id = dc.customer_id
    GROUP BY dc.customer_unique_id
)
SELECT
    order_count,
    COUNT(*) AS customer_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM customer_orders
GROUP BY order_count
ORDER BY order_count;


-- ── 7. Repeat Customers (≥ 2 orders) ─────────────────────────
SELECT
    COUNT(*) AS repeat_customer_count
FROM (
    SELECT dc.customer_unique_id
    FROM fact_sales fs
    JOIN dim_customer dc ON fs.customer_id = dc.customer_id
    GROUP BY dc.customer_unique_id
    HAVING COUNT(DISTINCT fs.order_id) >= 2
) sub;


-- ── 8. Top 10 Sellers by Revenue ─────────────────────────────
SELECT
    ds.seller_id,
    ds.seller_state,
    COUNT(DISTINCT fs.order_id)        AS total_orders,
    ROUND(SUM(fs.revenue)::NUMERIC, 2) AS total_revenue
FROM fact_sales fs
JOIN dim_seller ds ON fs.seller_id = ds.seller_id
GROUP BY ds.seller_id, ds.seller_state
ORDER BY total_revenue DESC
LIMIT 10;


-- ── 9. Late Deliveries by State ───────────────────────────────
SELECT
    dc.customer_state,
    COUNT(*)                                        AS total_orders,
    SUM(fs.late_delivery)                           AS late_orders,
    ROUND(100.0 * SUM(fs.late_delivery) / COUNT(*), 2) AS late_pct
FROM fact_sales fs
JOIN dim_customer dc ON fs.customer_id = dc.customer_id
WHERE fs.order_status = 'delivered'
GROUP BY dc.customer_state
ORDER BY late_pct DESC;


-- ── 10. Month-over-Month Revenue Growth ──────────────────────
WITH monthly AS (
    SELECT
        dd.year,
        dd.month,
        SUM(fs.revenue) AS revenue
    FROM fact_sales fs
    JOIN dim_date dd ON fs.date_id = dd.date_id
    WHERE fs.order_status = 'delivered'
    GROUP BY dd.year, dd.month
)
SELECT
    year,
    month,
    ROUND(revenue::NUMERIC, 2) AS revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY year, month))
              / NULLIF(LAG(revenue) OVER (ORDER BY year, month), 0),
        2
    ) AS mom_growth_pct
FROM monthly
ORDER BY year, month;


-- ── 11. Revenue by Category ───────────────────────────────────
SELECT
    dp.product_category_name,
    COUNT(DISTINCT fs.order_id)        AS total_orders,
    ROUND(SUM(fs.revenue)::NUMERIC, 2) AS category_revenue
FROM fact_sales fs
JOIN dim_product dp ON fs.product_id = dp.product_id
GROUP BY dp.product_category_name
ORDER BY category_revenue DESC
LIMIT 20;


-- ── 12. Revenue Rank per Customer (Window Function) ──────────
SELECT
    dc.customer_unique_id,
    dc.customer_state,
    ROUND(SUM(fs.revenue)::NUMERIC, 2) AS total_revenue,
    RANK() OVER (ORDER BY SUM(fs.revenue) DESC) AS revenue_rank,
    DENSE_RANK() OVER (PARTITION BY dc.customer_state ORDER BY SUM(fs.revenue) DESC) AS state_rank
FROM fact_sales fs
JOIN dim_customer dc ON fs.customer_id = dc.customer_id
GROUP BY dc.customer_unique_id, dc.customer_state
ORDER BY revenue_rank
LIMIT 50;


-- ── 13. Running Total Revenue (Window Function) ───────────────
SELECT
    dd.year,
    dd.month,
    ROUND(SUM(fs.revenue)::NUMERIC, 2)                                  AS monthly_revenue,
    ROUND(SUM(SUM(fs.revenue)) OVER (ORDER BY dd.year, dd.month)::NUMERIC, 2) AS running_total
FROM fact_sales fs
JOIN dim_date dd ON fs.date_id = dd.date_id
WHERE fs.order_status = 'delivered'
GROUP BY dd.year, dd.month
ORDER BY dd.year, dd.month;


-- ── 14. Average Review Score by Category ─────────────────────
SELECT
    dp.product_category_name,
    ROUND(AVG(fs.review_score)::NUMERIC, 2) AS avg_review_score,
    COUNT(*)                                 AS review_count
FROM fact_sales fs
JOIN dim_product dp ON fs.product_id = dp.product_id
WHERE fs.review_score IS NOT NULL
GROUP BY dp.product_category_name
ORDER BY avg_review_score DESC;


-- ── 15. Views ─────────────────────────────────────────────────

CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    dd.year,
    dd.month,
    dd.month_name,
    ROUND(SUM(fs.revenue)::NUMERIC, 2) AS monthly_revenue,
    COUNT(DISTINCT fs.order_id)        AS order_count
FROM fact_sales fs
JOIN dim_date dd ON fs.date_id = dd.date_id
WHERE fs.order_status = 'delivered'
GROUP BY dd.year, dd.month, dd.month_name;


CREATE OR REPLACE VIEW vw_top_products AS
SELECT
    dp.product_id,
    dp.product_category_name,
    COUNT(*)                           AS times_sold,
    ROUND(SUM(fs.revenue)::NUMERIC, 2) AS total_revenue,
    ROUND(AVG(fs.review_score)::NUMERIC, 2) AS avg_review
FROM fact_sales fs
JOIN dim_product dp ON fs.product_id = dp.product_id
GROUP BY dp.product_id, dp.product_category_name;


CREATE OR REPLACE VIEW vw_customer_summary AS
SELECT
    dc.customer_unique_id,
    dc.customer_state,
    COUNT(DISTINCT fs.order_id)        AS total_orders,
    ROUND(SUM(fs.revenue)::NUMERIC, 2) AS lifetime_value,
    ROUND(AVG(fs.review_score)::NUMERIC, 2) AS avg_review
FROM fact_sales fs
JOIN dim_customer dc ON fs.customer_id = dc.customer_id
GROUP BY dc.customer_unique_id, dc.customer_state;
