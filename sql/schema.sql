-- ============================================================
-- sales_db  –  Schema Definition
-- ============================================================

-- ── Raw / staging tables ─────────────────────────────────────

CREATE TABLE IF NOT EXISTS customers (
    customer_id             VARCHAR(50)  PRIMARY KEY,
    customer_unique_id      VARCHAR(50),
    customer_zip_code_prefix VARCHAR(10),
    customer_city           VARCHAR(100),
    customer_state          CHAR(2)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id                        VARCHAR(50)  PRIMARY KEY,
    customer_id                     VARCHAR(50)  REFERENCES customers(customer_id),
    order_status                    VARCHAR(30),
    order_purchase_timestamp        TIMESTAMP,
    order_approved_at               TIMESTAMP,
    order_delivered_carrier_date    TIMESTAMP,
    order_delivered_customer_date   TIMESTAMP,
    order_estimated_delivery_date   TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id                  VARCHAR(50)  PRIMARY KEY,
    product_category_name       VARCHAR(100),
    product_name_length         INTEGER,
    product_description_length  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            NUMERIC(10,2),
    product_length_cm           NUMERIC(10,2),
    product_height_cm           NUMERIC(10,2),
    product_width_cm            NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS sellers (
    seller_id               VARCHAR(50)  PRIMARY KEY,
    seller_zip_code_prefix  VARCHAR(10),
    seller_city             VARCHAR(100),
    seller_state            CHAR(2)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id            VARCHAR(50)  REFERENCES orders(order_id),
    order_item_id       INTEGER,
    product_id          VARCHAR(50)  REFERENCES products(product_id),
    seller_id           VARCHAR(50)  REFERENCES sellers(seller_id),
    shipping_limit_date TIMESTAMP,
    price               NUMERIC(12,2),
    freight_value       NUMERIC(12,2),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS payments (
    order_id                VARCHAR(50)  REFERENCES orders(order_id),
    payment_sequential      INTEGER,
    payment_type            VARCHAR(30),
    payment_installments    INTEGER,
    payment_value           NUMERIC(12,2),
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id               VARCHAR(50)  PRIMARY KEY,
    order_id                VARCHAR(50)  REFERENCES orders(order_id),
    review_score            SMALLINT,
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

-- ── Star Schema ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id             VARCHAR(50)  PRIMARY KEY,
    customer_unique_id      VARCHAR(50),
    customer_city           VARCHAR(100),
    customer_state          CHAR(2),
    customer_zip_code_prefix VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id                  VARCHAR(50)  PRIMARY KEY,
    product_category_name       VARCHAR(100),
    product_name_length         INTEGER,
    product_description_length  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            NUMERIC(10,2),
    product_length_cm           NUMERIC(10,2),
    product_height_cm           NUMERIC(10,2),
    product_width_cm            NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS dim_seller (
    seller_id               VARCHAR(50)  PRIMARY KEY,
    seller_zip_code_prefix  VARCHAR(10),
    seller_city             VARCHAR(100),
    seller_state            CHAR(2)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id     INTEGER      PRIMARY KEY,
    full_date   DATE,
    year        SMALLINT,
    quarter     SMALLINT,
    month       SMALLINT,
    month_name  VARCHAR(15),
    week        SMALLINT,
    day         SMALLINT,
    day_of_week VARCHAR(10),
    is_weekend  SMALLINT
);

CREATE TABLE IF NOT EXISTS fact_sales (
    fact_id             BIGSERIAL    PRIMARY KEY,
    order_id            VARCHAR(50),
    order_item_id       INTEGER,
    customer_id         VARCHAR(50)  REFERENCES dim_customer(customer_id),
    product_id          VARCHAR(50)  REFERENCES dim_product(product_id),
    seller_id           VARCHAR(50)  REFERENCES dim_seller(seller_id),
    date_id             INTEGER      REFERENCES dim_date(date_id),
    price               NUMERIC(12,2),
    freight_value       NUMERIC(12,2),
    payment_value       NUMERIC(12,2),
    payment_type        VARCHAR(30),
    review_score        SMALLINT,
    order_status        VARCHAR(30),
    delivery_time_days  INTEGER,
    late_delivery       SMALLINT,
    revenue             NUMERIC(12,2),
    profit              NUMERIC(12,2)
);

-- ── Indexes ───────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_fact_customer   ON fact_sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_product    ON fact_sales(product_id);
CREATE INDEX IF NOT EXISTS idx_fact_seller     ON fact_sales(seller_id);
CREATE INDEX IF NOT EXISTS idx_fact_date       ON fact_sales(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_status     ON fact_sales(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_items_product   ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_items_seller    ON order_items(seller_id);
