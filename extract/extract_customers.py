"""
Extract Customers
Reads the raw customers CSV file into a Pandas DataFrame.
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
logger = logging.getLogger("extract_customers")

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def extract_customers(filepath: str | None = None) -> pd.DataFrame:
    """
    Load customers from CSV into a DataFrame.

    Parameters
    ----------
    filepath : str, optional
        Path to CSV. Defaults to data/raw/olist_customers_dataset.csv

    Returns
    -------
    pd.DataFrame
    """
    if filepath is None:
        filepath = os.path.join(RAW_DIR, "olist_customers_dataset.csv")

    filepath = os.path.abspath(filepath)
    logger.info("Extraction started — customers")
    logger.info("Reading file: %s", filepath)

    if not os.path.exists(filepath):
        logger.error("File not found: %s", filepath)
        raise FileNotFoundError(f"Customers CSV not found at: {filepath}")

    try:
        df = pd.read_csv(filepath, encoding="utf-8")
    except UnicodeDecodeError:
        logger.warning("UTF-8 decoding failed, retrying with latin-1")
        df = pd.read_csv(filepath, encoding="latin-1")

    logger.info("Customers loaded — %d rows, %d columns", len(df), len(df.columns))
    return df


if __name__ == "__main__":
    customers = extract_customers()
    print(customers.head())
