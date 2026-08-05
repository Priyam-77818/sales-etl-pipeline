"""
Airflow DAG  –  Sales ETL Pipeline
Runs every day at 08:00 UTC.

Task order:
  extract  →  validate  →  clean  →  transform  →  load  →  backup  →  notify
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

logger = logging.getLogger(__name__)

# ── Default DAG arguments ──────────────────────────────────────────────────────
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email": ["alerts@yourcompany.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# ── Task functions ─────────────────────────────────────────────────────────────

def task_extract(**context) -> None:
    """Extract all raw CSVs."""
    from extract.extract_orders import extract_orders
    from extract.extract_customers import extract_customers
    from extract.extract_products import (
        extract_products, extract_payments,
        extract_reviews, extract_items, extract_sellers,
    )

    logger.info("Extraction started")
    orders    = extract_orders()
    customers = extract_customers()
    products  = extract_products()
    payments  = extract_payments()
    reviews   = extract_reviews()
    items     = extract_items()
    sellers   = extract_sellers()

    # Push row counts to XCom for monitoring
    context["ti"].xcom_push("row_counts", {
        "orders":    len(orders),
        "customers": len(customers),
        "products":  len(products),
        "payments":  len(payments),
        "reviews":   len(reviews),
        "items":     len(items),
        "sellers":   len(sellers),
    })
    logger.info("Extraction complete")


def task_validate(**context) -> None:
    """Validate orders and customers."""
    from extract.extract_orders import extract_orders
    from extract.extract_customers import extract_customers
    from validation.validate_orders import validate_orders
    from validation.validate_customers import validate_customers

    logger.info("Validation started")
    validate_orders(extract_orders())
    validate_customers(extract_customers())
    logger.info("Validation complete")


def task_clean(**context) -> None:
    """Clean all datasets."""
    from extract.extract_orders import extract_orders
    from extract.extract_customers import extract_customers
    from extract.extract_products import (
        extract_products, extract_payments,
        extract_reviews, extract_items, extract_sellers,
    )
    from transform.clean_orders import (
        clean_orders, clean_customers, clean_products,
        clean_items, clean_payments, clean_reviews, clean_sellers,
    )

    logger.info("Cleaning started")
    clean_orders(extract_orders())
    clean_customers(extract_customers())
    clean_products(extract_products())
    clean_items(extract_items())
    clean_payments(extract_payments())
    clean_reviews(extract_reviews())
    clean_sellers(extract_sellers())
    logger.info("Cleaning complete")


def task_transform(**context) -> None:
    """Feature engineering and star schema construction."""
    import pandas as pd

    CLEANED = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cleaned")

    logger.info("Transformation started")

    orders    = pd.read_csv(os.path.join(CLEANED, "orders_cleaned.csv"))
    customers = pd.read_csv(os.path.join(CLEANED, "customers_cleaned.csv"))
    products  = pd.read_csv(os.path.join(CLEANED, "products_cleaned.csv"))
    payments  = pd.read_csv(os.path.join(CLEANED, "payments_cleaned.csv"))
    reviews   = pd.read_csv(os.path.join(CLEANED, "reviews_cleaned.csv"))
    items     = pd.read_csv(os.path.join(CLEANED, "items_cleaned.csv"))
    sellers   = pd.read_csv(os.path.join(CLEANED, "sellers_cleaned.csv"))

    from transform.feature_engineering import build_order_features
    from transform.star_schema import (
        build_dim_customer, build_dim_product, build_dim_seller,
        build_dim_date, build_fact_sales,
    )

    build_order_features(orders, items, customers)
    build_dim_customer(customers)
    build_dim_product(products)
    build_dim_seller(sellers)
    build_dim_date(orders)
    build_fact_sales(orders, items, payments, reviews)

    logger.info("Transformation complete")


def task_load(**context) -> None:
    """Load all tables into PostgreSQL."""
    import pandas as pd

    CLEANED     = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cleaned")
    TRANSFORMED = os.path.join(os.path.dirname(__file__), "..", "..", "data", "transformed")

    logger.info("Loading into PostgreSQL started")

    from load.postgres_loader import get_engine, load_all, check_connection

    engine = get_engine()
    if not check_connection(engine):
        raise ConnectionError("Cannot connect to PostgreSQL")

    load_all(
        customers   = pd.read_csv(os.path.join(CLEANED, "customers_cleaned.csv")),
        orders      = pd.read_csv(os.path.join(CLEANED, "orders_cleaned.csv")),
        products    = pd.read_csv(os.path.join(CLEANED, "products_cleaned.csv")),
        payments    = pd.read_csv(os.path.join(CLEANED, "payments_cleaned.csv")),
        reviews     = pd.read_csv(os.path.join(CLEANED, "reviews_cleaned.csv")),
        items       = pd.read_csv(os.path.join(CLEANED, "items_cleaned.csv")),
        sellers     = pd.read_csv(os.path.join(CLEANED, "sellers_cleaned.csv")),
        fact_sales  = pd.read_csv(os.path.join(TRANSFORMED, "fact_sales.csv")),
        dim_customer= pd.read_csv(os.path.join(TRANSFORMED, "dim_customer.csv")),
        dim_product = pd.read_csv(os.path.join(TRANSFORMED, "dim_product.csv")),
        dim_seller  = pd.read_csv(os.path.join(TRANSFORMED, "dim_seller.csv")),
        dim_date    = pd.read_csv(os.path.join(TRANSFORMED, "dim_date.csv")),
        engine      = engine,
    )
    logger.info("Loaded into PostgreSQL successfully")


def task_backup(**context) -> None:
    """Upload processed files to AWS S3."""
    import boto3
    import glob

    BUCKET = os.getenv("S3_BUCKET", "sales-etl-pipeline")
    logger.info("S3 backup started — bucket: %s", BUCKET)

    s3 = boto3.client(
        "s3",
        aws_access_key_id     = os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name           = os.getenv("AWS_REGION", "us-east-1"),
    )

    BASE = os.path.join(os.path.dirname(__file__), "..", "..")

    upload_map = {
        "cleaned":    os.path.join(BASE, "data", "cleaned", "*.csv"),
        "transformed": os.path.join(BASE, "data", "transformed", "*.csv"),
        "logs":       os.path.join(BASE, "logs", "*.log"),
    }

    for s3_prefix, pattern in upload_map.items():
        for local_path in glob.glob(pattern):
            key = f"{s3_prefix}/{os.path.basename(local_path)}"
            s3.upload_file(local_path, BUCKET, key)
            logger.info("Uploaded: s3://%s/%s", BUCKET, key)

    logger.info("S3 backup complete")


def task_notify(**context) -> None:
    """Log pipeline completion."""
    logger.info("Pipeline Finished Successfully — %s", datetime.utcnow().isoformat())


# ── DAG definition ─────────────────────────────────────────────────────────────
with DAG(
    dag_id="sales_etl_pipeline",
    default_args=default_args,
    description="Cloud-Native ETL Pipeline for E-Commerce Sales Analytics",
    schedule_interval="0 8 * * *",   # Daily at 08:00 UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["etl", "sales", "e-commerce"],
) as dag:

    extract   = PythonOperator(task_id="extract",   python_callable=task_extract)
    validate  = PythonOperator(task_id="validate",  python_callable=task_validate)
    clean     = PythonOperator(task_id="clean",     python_callable=task_clean)
    transform = PythonOperator(task_id="transform", python_callable=task_transform)
    load      = PythonOperator(task_id="load",      python_callable=task_load)
    backup    = PythonOperator(task_id="backup",    python_callable=task_backup)
    notify    = PythonOperator(task_id="notify",    python_callable=task_notify)

    # Pipeline order
    extract >> validate >> clean >> transform >> load >> backup >> notify
