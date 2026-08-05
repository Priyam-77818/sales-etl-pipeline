"""
Feature Engineering
Creates derived columns:
  - revenue, month, year, quarter
  - customer_lifetime_value
  - average_order_value
  - delivery_time_days
  - is_repeat_customer
  - profit (estimated)
  - discount_pct
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
logger = logging.getLogger("feature_engineering")

TRANSFORMED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "transformed")


def build_order_features(
    orders: pd.DataFrame,
    items: pd.DataFrame,
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join orders + items + customers and engineer features.

    Parameters
    ----------
    orders : pd.DataFrame  Cleaned orders
    items  : pd.DataFrame  Cleaned order items
    customers : pd.DataFrame  Cleaned customers

    Returns
    -------
    pd.DataFrame  Enriched orders DataFrame
    """
    logger.info("Feature engineering started")

    # ── Aggregate items per order ──────────────────────────────────────────────
    items_agg = (
        items.groupby("order_id")
        .agg(
            revenue=("price", "sum"),
            freight=("freight_value", "sum"),
            item_count=("order_item_id", "count"),
        )
        .reset_index()
    )

    # ── Merge orders with item aggregates ─────────────────────────────────────
    df = orders.merge(items_agg, on="order_id", how="left")
    df = df.merge(customers[["customer_id", "customer_unique_id", "customer_state"]], on="customer_id", how="left")

    # ── Time features ──────────────────────────────────────────────────────────
    if "order_purchase_timestamp" in df.columns:
        df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"], errors="coerce")
        df["month"] = df["order_purchase_timestamp"].dt.month
        df["year"] = df["order_purchase_timestamp"].dt.year
        df["quarter"] = df["order_purchase_timestamp"].dt.quarter
        df["day_of_week"] = df["order_purchase_timestamp"].dt.day_name()
        logger.info("Time features added")

    # ── Delivery time ──────────────────────────────────────────────────────────
    if "order_delivered_customer_date" in df.columns and "order_purchase_timestamp" in df.columns:
        df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"], errors="coerce")
        df["delivery_time_days"] = (
            df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
        ).dt.days
        df["delivery_time_days"] = df["delivery_time_days"].clip(lower=0)
        logger.info("Delivery time computed")

    # ── Estimated vs actual delivery ──────────────────────────────────────────
    if "order_estimated_delivery_date" in df.columns and "order_delivered_customer_date" in df.columns:
        df["order_estimated_delivery_date"] = pd.to_datetime(df["order_estimated_delivery_date"], errors="coerce")
        df["late_delivery"] = (
            df["order_delivered_customer_date"] > df["order_estimated_delivery_date"]
        ).astype(int)
        logger.info("Late delivery flag added")

    # ── Profit (estimated at 30% margin) ──────────────────────────────────────
    if "revenue" in df.columns:
        df["revenue"] = df["revenue"].fillna(0)
        df["profit"] = (df["revenue"] * 0.30).round(2)
        logger.info("Profit column added")

    # ── Discount % (placeholder — dataset doesn't have list price) ────────────
    df["discount_pct"] = 0.0

    # ── Average Order Value per customer ──────────────────────────────────────
    if "customer_unique_id" in df.columns and "revenue" in df.columns:
        aov = (
            df.groupby("customer_unique_id")["revenue"]
            .mean()
            .rename("avg_order_value")
            .reset_index()
        )
        df = df.merge(aov, on="customer_unique_id", how="left")
        logger.info("Average order value computed")

    # ── Customer Lifetime Value ────────────────────────────────────────────────
    if "customer_unique_id" in df.columns and "revenue" in df.columns:
        clv = (
            df.groupby("customer_unique_id")["revenue"]
            .sum()
            .rename("customer_lifetime_value")
            .reset_index()
        )
        df = df.merge(clv, on="customer_unique_id", how="left")
        logger.info("Customer lifetime value computed")

    # ── Repeat customer flag ───────────────────────────────────────────────────
    if "customer_unique_id" in df.columns:
        order_counts = df.groupby("customer_unique_id")["order_id"].count().rename("order_count")
        df = df.merge(order_counts.reset_index(), on="customer_unique_id", how="left")
        df["is_repeat_customer"] = (df["order_count"] > 1).astype(int)
        logger.info("Repeat customer flag added")

    logger.info("Feature engineering complete — %d rows, %d columns", len(df), len(df.columns))
    _save(df, "orders_featured.csv")
    return df


def _save(df: pd.DataFrame, filename: str) -> None:
    os.makedirs(TRANSFORMED_DIR, exist_ok=True)
    path = os.path.join(TRANSFORMED_DIR, filename)
    df.to_csv(path, index=False)
    logger.info("Saved: %s", path)
