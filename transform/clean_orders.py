"""
Clean Orders
Removes duplicates, fills / drops nulls, converts dates,
normalises strings, and removes price outliers.
Saves cleaned CSVs to data/cleaned/.
"""

import os
import logging
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "logs", "pipeline.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("clean_orders")

CLEANED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned")

DATE_COLUMNS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw orders DataFrame.

    Steps
    -----
    1. Drop exact duplicates
    2. Drop duplicate order IDs (keep first)
    3. Drop rows with null customer_id or order_id
    4. Convert date columns to datetime
    5. Normalise string columns to lowercase + strip

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame  Cleaned orders DataFrame.
    """
    logger.info("Cleaning started — orders (%d rows)", len(df))
    original_len = len(df)

    # 1. Remove exact duplicates
    df = df.drop_duplicates()
    logger.info("Duplicates removed: %d rows dropped", original_len - len(df))

    # 2. Drop duplicate order IDs
    df = df.drop_duplicates(subset=["order_id"], keep="first")

    # 3. Drop rows with critical nulls
    df = df.dropna(subset=["order_id", "customer_id"])
    logger.info("Rows after null drop: %d", len(df))

    # 4. Convert dates
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    logger.info("Date columns converted")

    # 5. Normalise string columns
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip().str.lower()
    logger.info("String columns normalised")

    logger.info("Cleaning complete — orders (%d rows)", len(df))
    _save(df, "orders_cleaned.csv")
    return df


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw customers DataFrame.
    """
    logger.info("Cleaning started — customers (%d rows)", len(df))

    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    df = df.dropna(subset=["customer_id"])

    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip().str.lower()

    # Ensure zip code is string with leading zeros
    if "customer_zip_code_prefix" in df.columns:
        df["customer_zip_code_prefix"] = (
            df["customer_zip_code_prefix"].astype(str).str.zfill(5)
        )

    logger.info("Cleaning complete — customers (%d rows)", len(df))
    _save(df, "customers_cleaned.csv")
    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw products DataFrame.
    Fills missing numeric fields with median, normalises strings.
    """
    logger.info("Cleaning started — products (%d rows)", len(df))

    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["product_id"], keep="first")
    df = df.dropna(subset=["product_id"])

    # Fill missing numeric columns with median
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        df[col] = df[col].fillna(df[col].median())

    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip().str.lower()
        df[col] = df[col].fillna("unknown")

    logger.info("Cleaning complete — products (%d rows)", len(df))
    _save(df, "products_cleaned.csv")
    return df


def clean_items(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean order items DataFrame.
    Removes rows with negative prices or freight values.
    """
    logger.info("Cleaning started — items (%d rows)", len(df))

    df = df.drop_duplicates()
    df = df.dropna(subset=["order_id", "product_id"])

    # Remove invalid prices
    if "price" in df.columns:
        before = len(df)
        df = df[df["price"] > 0]
        logger.info("Removed %d rows with non-positive price", before - len(df))

    if "freight_value" in df.columns:
        df = df[df["freight_value"] >= 0]

    # Remove outliers using IQR on price
    if "price" in df.columns:
        Q1 = df["price"].quantile(0.01)
        Q3 = df["price"].quantile(0.99)
        df = df[(df["price"] >= Q1) & (df["price"] <= Q3)]

    # Convert date columns
    if "shipping_limit_date" in df.columns:
        df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")

    logger.info("Cleaning complete — items (%d rows)", len(df))
    _save(df, "items_cleaned.csv")
    return df


def clean_payments(df: pd.DataFrame) -> pd.DataFrame:
    """Clean payments DataFrame."""
    logger.info("Cleaning started — payments (%d rows)", len(df))

    df = df.drop_duplicates()
    df = df.dropna(subset=["order_id"])

    if "payment_value" in df.columns:
        df = df[df["payment_value"] >= 0]

    if "payment_installments" in df.columns:
        df["payment_installments"] = df["payment_installments"].fillna(1).astype(int)

    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip().str.lower()

    logger.info("Cleaning complete — payments (%d rows)", len(df))
    _save(df, "payments_cleaned.csv")
    return df


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Clean reviews DataFrame."""
    logger.info("Cleaning started — reviews (%d rows)", len(df))

    df = df.drop_duplicates()
    df = df.dropna(subset=["order_id"])

    for col in ["review_creation_date", "review_answer_timestamp"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "review_score" in df.columns:
        df = df[df["review_score"].between(1, 5)]

    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip().str.lower()
        df[col] = df[col].fillna("")

    logger.info("Cleaning complete — reviews (%d rows)", len(df))
    _save(df, "reviews_cleaned.csv")
    return df


def clean_sellers(df: pd.DataFrame) -> pd.DataFrame:
    """Clean sellers DataFrame."""
    logger.info("Cleaning started — sellers (%d rows)", len(df))

    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["seller_id"], keep="first")

    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip().str.lower()

    if "seller_zip_code_prefix" in df.columns:
        df["seller_zip_code_prefix"] = (
            df["seller_zip_code_prefix"].astype(str).str.zfill(5)
        )

    logger.info("Cleaning complete — sellers (%d rows)", len(df))
    _save(df, "sellers_cleaned.csv")
    return df


def _save(df: pd.DataFrame, filename: str) -> None:
    os.makedirs(CLEANED_DIR, exist_ok=True)
    path = os.path.join(CLEANED_DIR, filename)
    df.to_csv(path, index=False)
    logger.info("Saved: %s (%d rows)", path, len(df))
