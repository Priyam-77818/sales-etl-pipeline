"""
run_pipeline.py
===============
End-to-end pipeline runner.
Execute directly (outside Airflow) for local development and testing.

Usage:
    python run_pipeline.py
    python run_pipeline.py --skip-s3        # skip AWS backup
    python run_pipeline.py --skip-db        # skip PostgreSQL load
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "logs", "pipeline.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("run_pipeline")


def parse_args():
    parser = argparse.ArgumentParser(description="Sales ETL Pipeline")
    parser.add_argument("--skip-s3", action="store_true", help="Skip AWS S3 backup")
    parser.add_argument("--skip-db", action="store_true", help="Skip PostgreSQL load")
    return parser.parse_args()


def step(name: str):
    """Simple decorator-style context for logging a step."""
    class _Step:
        def __enter__(self):
            logger.info("=" * 60)
            logger.info("STEP: %s — started", name)
            self.t0 = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = time.time() - self.t0
            if exc_type:
                logger.error("STEP: %s — FAILED (%.1fs): %s", name, elapsed, exc_val)
            else:
                logger.info("STEP: %s — complete (%.1fs)", name, elapsed)
            return False  # re-raise exceptions

    return _Step()


def main():
    args = parse_args()
    pipeline_start = time.time()
    logger.info("Pipeline starting")

    # ── 1. Extract ────────────────────────────────────────────────────────────
    with step("Extract"):
        from extract.extract_orders import extract_orders
        from extract.extract_customers import extract_customers
        from extract.extract_products import (
            extract_products, extract_payments,
            extract_reviews, extract_items, extract_sellers,
        )
        orders    = extract_orders()
        customers = extract_customers()
        products  = extract_products()
        payments  = extract_payments()
        reviews   = extract_reviews()
        items     = extract_items()
        sellers   = extract_sellers()
        logger.info(
            "Rows loaded — orders: %d, customers: %d, products: %d, "
            "payments: %d, reviews: %d, items: %d, sellers: %d",
            len(orders), len(customers), len(products),
            len(payments), len(reviews), len(items), len(sellers),
        )

    # ── 2. Validate ───────────────────────────────────────────────────────────
    with step("Validate"):
        from validation.validate_orders import validate_orders
        from validation.validate_customers import validate_customers
        validate_orders(orders)
        validate_customers(customers)

    # ── 3. Clean ──────────────────────────────────────────────────────────────
    with step("Clean"):
        from transform.clean_orders import (
            clean_orders, clean_customers, clean_products,
            clean_items, clean_payments, clean_reviews, clean_sellers,
        )
        orders    = clean_orders(orders)
        customers = clean_customers(customers)
        products  = clean_products(products)
        items     = clean_items(items)
        payments  = clean_payments(payments)
        reviews   = clean_reviews(reviews)
        sellers   = clean_sellers(sellers)

    # ── 4. Transform ──────────────────────────────────────────────────────────
    with step("Transform"):
        from transform.feature_engineering import build_order_features
        from transform.star_schema import (
            build_dim_customer, build_dim_product, build_dim_seller,
            build_dim_date, build_fact_sales,
        )
        build_order_features(orders, items, customers)
        dim_customer = build_dim_customer(customers)
        dim_product  = build_dim_product(products)
        dim_seller   = build_dim_seller(sellers)
        dim_date     = build_dim_date(orders)
        fact_sales   = build_fact_sales(orders, items, payments, reviews)

    # ── 5. Load into PostgreSQL ───────────────────────────────────────────────
    if not args.skip_db:
        with step("Load into PostgreSQL"):
            from load.postgres_loader import get_engine, load_all, check_connection
            engine = get_engine()
            if check_connection(engine):
                load_all(
                    customers=customers, orders=orders, products=products,
                    payments=payments, reviews=reviews, items=items,
                    sellers=sellers, fact_sales=fact_sales,
                    dim_customer=dim_customer, dim_product=dim_product,
                    dim_seller=dim_seller, dim_date=dim_date,
                    engine=engine,
                )
                logger.info("Loaded into PostgreSQL successfully")
            else:
                logger.warning("Skipping DB load — connection failed")
    else:
        logger.info("PostgreSQL load skipped (--skip-db)")

    # ── 6. Backup to S3 ───────────────────────────────────────────────────────
    if not args.skip_s3:
        with step("Backup to S3"):
            from load.s3_backup import backup_all
            result = backup_all()
            logger.info("S3 backup result: %s", result)
    else:
        logger.info("S3 backup skipped (--skip-s3)")

    # ── Done ──────────────────────────────────────────────────────────────────
    total = time.time() - pipeline_start
    logger.info("=" * 60)
    logger.info("Pipeline Finished Successfully — total time: %.1fs", total)


if __name__ == "__main__":
    main()
