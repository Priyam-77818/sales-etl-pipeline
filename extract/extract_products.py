"""
Extract Products
Reads raw products, payments, reviews, and order-items CSVs.
"""

import os
import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "logs", "pipeline.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("extract_products")

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def _load_csv(filename: str) -> pd.DataFrame:
    """Helper: load a CSV with UTF-8 fallback to latin-1."""
    filepath = os.path.abspath(os.path.join(RAW_DIR, filename))
    logger.info("Reading file: %s", filepath)

    if not os.path.exists(filepath):
        logger.error("File not found: %s", filepath)
        raise FileNotFoundError(f"CSV not found at: {filepath}")

    try:
        return pd.read_csv(filepath, encoding="utf-8")
    except UnicodeDecodeError:
        logger.warning("UTF-8 decoding failed, retrying with latin-1")
        return pd.read_csv(filepath, encoding="latin-1")


def extract_products() -> pd.DataFrame:
    """Load olist_products_dataset.csv."""
    logger.info("Extraction started — products")
    df = _load_csv("olist_products_dataset.csv")
    logger.info("Products loaded — %d rows", len(df))
    return df


def extract_payments() -> pd.DataFrame:
    """Load olist_order_payments_dataset.csv."""
    logger.info("Extraction started — payments")
    df = _load_csv("olist_order_payments_dataset.csv")
    logger.info("Payments loaded — %d rows", len(df))
    return df


def extract_reviews() -> pd.DataFrame:
    """Load olist_order_reviews_dataset.csv."""
    logger.info("Extraction started — reviews")
    df = _load_csv("olist_order_reviews_dataset.csv")
    logger.info("Reviews loaded — %d rows", len(df))
    return df


def extract_items() -> pd.DataFrame:
    """Load olist_order_items_dataset.csv."""
    logger.info("Extraction started — order items")
    df = _load_csv("olist_order_items_dataset.csv")
    logger.info("Order items loaded — %d rows", len(df))
    return df


def extract_sellers() -> pd.DataFrame:
    """Load olist_sellers_dataset.csv."""
    logger.info("Extraction started — sellers")
    df = _load_csv("olist_sellers_dataset.csv")
    logger.info("Sellers loaded — %d rows", len(df))
    return df


if __name__ == "__main__":
    print(extract_products().head())
    print(extract_payments().head())
    print(extract_items().head())
