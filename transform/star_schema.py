"""
Star Schema Builder
Creates:
  - dim_customer
  - dim_product
  - dim_date
  - dim_seller
  - fact_sales
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
logger = logging.getLogger("star_schema")

TRANSFORMED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "transformed")


# ── Dimension: Customer ────────────────────────────────────────────────────────

def build_dim_customer(customers: pd.DataFrame) -> pd.DataFrame:
    """
    Build the customer dimension table.

    Columns: customer_id, customer_unique_id, customer_city,
             customer_state, customer_zip_code_prefix
    """
    logger.info("Building dim_customer")
    cols = [c for c in [
        "customer_id", "customer_unique_id",
        "customer_city", "customer_state", "customer_zip_code_prefix"
    ] if c in customers.columns]

    dim = customers[cols].drop_duplicates(subset=["customer_id"])
    dim = dim.reset_index(drop=True)
    logger.info("dim_customer — %d rows", len(dim))
    _save(dim, "dim_customer.csv")
    return dim


# ── Dimension: Product ────────────────────────────────────────────────────────

def build_dim_product(products: pd.DataFrame) -> pd.DataFrame:
    """
    Build the product dimension table.

    Columns: product_id, product_category_name,
             product_name_length, product_description_length,
             product_photos_qty, product_weight_g, product_length_cm,
             product_height_cm, product_width_cm
    """
    logger.info("Building dim_product")
    cols = [c for c in [
        "product_id", "product_category_name",
        "product_name_lenght", "product_description_lenght",
        "product_photos_qty", "product_weight_g",
        "product_length_cm", "product_height_cm", "product_width_cm"
    ] if c in products.columns]

    dim = products[cols].drop_duplicates(subset=["product_id"])
    # Rename typo columns if present
    dim = dim.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    })
    dim = dim.reset_index(drop=True)
    logger.info("dim_product — %d rows", len(dim))
    _save(dim, "dim_product.csv")
    return dim


# ── Dimension: Seller ────────────────────────────────────────────────────────

def build_dim_seller(sellers: pd.DataFrame) -> pd.DataFrame:
    """
    Build the seller dimension table.

    Columns: seller_id, seller_zip_code_prefix, seller_city, seller_state
    """
    logger.info("Building dim_seller")
    cols = [c for c in [
        "seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"
    ] if c in sellers.columns]

    dim = sellers[cols].drop_duplicates(subset=["seller_id"])
    dim = dim.reset_index(drop=True)
    logger.info("dim_seller — %d rows", len(dim))
    _save(dim, "dim_seller.csv")
    return dim


# ── Dimension: Date ────────────────────────────────────────────────────────────

def build_dim_date(orders: pd.DataFrame) -> pd.DataFrame:
    """
    Build the date dimension from order purchase timestamps.

    Columns: date_id, full_date, year, quarter, month, month_name,
             week, day, day_of_week, is_weekend
    """
    logger.info("Building dim_date")

    ts = pd.to_datetime(orders["order_purchase_timestamp"], errors="coerce").dropna()
    dates = ts.dt.normalize().drop_duplicates().sort_values().reset_index(drop=True)

    dim = pd.DataFrame()
    dim["full_date"] = dates
    dim["year"] = dates.dt.year
    dim["quarter"] = dates.dt.quarter
    dim["month"] = dates.dt.month
    dim["month_name"] = dates.dt.month_name()
    dim["week"] = dates.dt.isocalendar().week.astype(int)
    dim["day"] = dates.dt.day
    dim["day_of_week"] = dates.dt.day_name()
    dim["is_weekend"] = dates.dt.dayofweek.isin([5, 6]).astype(int)
    dim["date_id"] = dim["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim = dim[["date_id", "full_date", "year", "quarter", "month",
               "month_name", "week", "day", "day_of_week", "is_weekend"]]

    logger.info("dim_date — %d rows", len(dim))
    _save(dim, "dim_date.csv")
    return dim


# ── Fact: Sales ───────────────────────────────────────────────────────────────

def build_fact_sales(
    orders: pd.DataFrame,
    items: pd.DataFrame,
    payments: pd.DataFrame,
    reviews: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the fact_sales table.

    Grain: one row per order_item.

    Columns: fact_id, order_id, order_item_id, customer_id, product_id,
             seller_id, date_id, price, freight_value, payment_value,
             payment_type, review_score, order_status, delivery_time_days,
             late_delivery, revenue, profit
    """
    logger.info("Building fact_sales")

    # Start from items (grain: order × item)
    fact = items.copy()

    # Merge order metadata
    order_cols = [c for c in [
        "order_id", "customer_id", "order_status",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ] if c in orders.columns]
    fact = fact.merge(orders[order_cols], on="order_id", how="left")

    # Merge payment aggregate (sum per order)
    if not payments.empty:
        pay_agg = (
            payments.groupby("order_id")
            .agg(payment_value=("payment_value", "sum"), payment_type=("payment_type", "first"))
            .reset_index()
        )
        fact = fact.merge(pay_agg, on="order_id", how="left")

    # Merge review score (first review per order)
    if not reviews.empty:
        rev = reviews.sort_values("review_creation_date").drop_duplicates(subset=["order_id"])
        fact = fact.merge(rev[["order_id", "review_score"]], on="order_id", how="left")

    # Date key
    if "order_purchase_timestamp" in fact.columns:
        fact["order_purchase_timestamp"] = pd.to_datetime(fact["order_purchase_timestamp"], errors="coerce")
        fact["date_id"] = fact["order_purchase_timestamp"].dt.strftime("%Y%m%d").astype("Int64")

    # Delivery time
    if "order_delivered_customer_date" in fact.columns and "order_purchase_timestamp" in fact.columns:
        fact["order_delivered_customer_date"] = pd.to_datetime(fact["order_delivered_customer_date"], errors="coerce")
        fact["delivery_time_days"] = (
            fact["order_delivered_customer_date"] - fact["order_purchase_timestamp"]
        ).dt.days.clip(lower=0)

    # Late delivery flag
    if "order_estimated_delivery_date" in fact.columns and "order_delivered_customer_date" in fact.columns:
        fact["order_estimated_delivery_date"] = pd.to_datetime(fact["order_estimated_delivery_date"], errors="coerce")
        fact["late_delivery"] = (
            fact["order_delivered_customer_date"] > fact["order_estimated_delivery_date"]
        ).astype("Int64")

    # Revenue and profit
    fact["revenue"] = (fact["price"].fillna(0) + fact["freight_value"].fillna(0)).round(2)
    fact["profit"] = (fact["price"].fillna(0) * 0.30).round(2)

    # Surrogate key
    fact = fact.reset_index(drop=True)
    fact.insert(0, "fact_id", fact.index + 1)

    # Keep only relevant columns
    keep_cols = [c for c in [
        "fact_id", "order_id", "order_item_id", "customer_id", "product_id",
        "seller_id", "date_id", "price", "freight_value", "payment_value",
        "payment_type", "review_score", "order_status", "delivery_time_days",
        "late_delivery", "revenue", "profit",
    ] if c in fact.columns]
    fact = fact[keep_cols]

    logger.info("fact_sales — %d rows, %d columns", len(fact), len(fact.columns))
    _save(fact, "fact_sales.csv")
    return fact


def _save(df: pd.DataFrame, filename: str) -> None:
    os.makedirs(TRANSFORMED_DIR, exist_ok=True)
    path = os.path.join(TRANSFORMED_DIR, filename)
    df.to_csv(path, index=False)
    logger.info("Saved: %s", path)
