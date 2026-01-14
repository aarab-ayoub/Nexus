-- warehouse.sql

DROP TABLE IF EXISTS fact_page_views;
DROP TABLE IF EXISTS fact_orders;

CREATE TABLE fact_orders (
    order_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    product_id VARCHAR(255),
    quantity INT,
    total_amount NUMERIC(10, 2),
    signup_date TIMESTAMP,
    country VARCHAR(255),
    category VARCHAR(255),
    product_price NUMERIC(10, 2)
);

CREATE TABLE fact_page_views (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    url VARCHAR(255),
    view_count BIGINT,
    PRIMARY KEY (window_start, url)
);