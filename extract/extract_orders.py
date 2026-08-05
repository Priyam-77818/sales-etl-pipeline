"""
Extract Orders
Reads the raw orders CSV file into a Pandas DataFrame.
Handles missing files, encoding issues, and logs each step.
"""

import os
import logging
import pandas as pd

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "logs", "pipeline.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("extract_orders")

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def extract_orders(filepath: str | None = None) -> pd.DataFrame:
    """
    Load orders from CSV into a DataFrame.

    Parameters
    ----------
    filepath : str, optional
        Absolute or relative path to the CSV file.
        Defaults to data/raw/olist_orders_dataset.csv

    Returns
    -------
    pd.DataFrame
        Raw orders DataFrame.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist at the given path.
    """
    if filepath is None:
        filepath = os.path.join(RAW_DIR, "olist_orders_dataset.csv")

    filepath = os.path.abspath(filepath)
    logger.info("Extraction started — orders")
    logger.info("Reading file: %s", filepath)

    if not os.path.exists(filepath):
        logger.error("File not found: %s", filepath)
        raise FileNotFoundError(f"Orders CSV not found at: {filepath}")

    try:
        df = pd.read_csv(filepath, encoding="utf-8")
    except UnicodeDecodeError:
        logger.warning("UTF-8 decoding failed, retrying with latin-1")
        df = pd.read_csv(filepath, encoding="latin-1")

    logger.info("Orders loaded — %d rows, %d columns", len(df), len(df.columns))
    return df


if __name__ == "__main__":
    orders = extract_orders()
    print(orders.head())
