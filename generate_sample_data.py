"""
generate_sample_data.py
=======================
Generates realistic sample CSVs into data/raw/ so you can run and test
the full pipeline without downloading the Kaggle dataset first.

Produces ~500 orders, ~400 customers, ~200 products, matching the
Olist schema exactly.

Usage:
    python generate_sample_data.py
    python generate_sample_data.py --rows 2000
"""

from __future__ import annotations

import argparse
import os
import random
import string
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")

STATES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO", "CE", "PE"]
CITIES = ["sao paulo", "rio de janeiro", "belo horizonte", "porto alegre",
          "curitiba", "florianopolis", "salvador", "goiania", "fortaleza", "recife"]
CATEGORIES = [
    "eletronicos", "cama_mesa_banho", "beleza_saude", "esporte_lazer",
    "informatica_acessorios", "moveis_decoracao", "utilidades_domesticas",
    "relogios_presentes", "ferramentas_jardim", "brinquedos",
]
PAYMENT_TYPES = ["credit_card", "boleto", "voucher", "debit_card"]
STATUSES = ["delivered", "delivered", "delivered", "shipped", "canceled",
            "invoiced", "processing"]  # weighted toward delivered


def uid() -> str:
    return uuid.uuid4().hex


def rand_date(start: datetime, days: int) -> datetime:
    return start + timedelta(days=random.randint(0, days),
                             hours=random.randint(0, 23),
                             minutes=random.randint(0, 59))


def generate(n_orders: int = 500) -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    rng = np.random.default_rng(42)
    base = datetime(2017, 1, 1)

    # ── Customers ─────────────────────────────────────────────────────────────
    n_customers = max(int(n_orders * 0.85), 50)
    customer_ids  = [uid() for _ in range(n_customers)]
    unique_ids    = [uid() for _ in range(n_customers)]
    state_picks   = rng.choice(len(STATES), n_customers)
    customers_df  = pd.DataFrame({
        "customer_id":             customer_ids,
        "customer_unique_id":      unique_ids,
        "customer_zip_code_prefix": rng.integers(10000, 99999, n_customers),
        "customer_city":           [CITIES[i] for i in state_picks],
        "customer_state":          [STATES[i] for i in state_picks],
    })
    customers_df.to_csv(os.path.join(RAW_DIR, "olist_customers_dataset.csv"), index=False)
    print(f"✓  customers        {len(customers_df):>5} rows")

    # ── Sellers ───────────────────────────────────────────────────────────────
    n_sellers  = max(int(n_orders * 0.1), 20)
    seller_ids = [uid() for _ in range(n_sellers)]
    s_picks    = rng.choice(len(STATES), n_sellers)
    sellers_df = pd.DataFrame({
        "seller_id":               seller_ids,
        "seller_zip_code_prefix":  rng.integers(10000, 99999, n_sellers),
        "seller_city":             [CITIES[i] for i in s_picks],
        "seller_state":            [STATES[i] for i in s_picks],
    })
    sellers_df.to_csv(os.path.join(RAW_DIR, "olist_sellers_dataset.csv"), index=False)
    print(f"✓  sellers          {len(sellers_df):>5} rows")

    # ── Products ──────────────────────────────────────────────────────────────
    n_products  = max(int(n_orders * 0.4), 100)
    product_ids = [uid() for _ in range(n_products)]
    products_df = pd.DataFrame({
        "product_id":                  product_ids,
        "product_category_name":       rng.choice(CATEGORIES, n_products),
        "product_name_lenght":         rng.integers(10, 60, n_products),
        "product_description_lenght":  rng.integers(50, 1000, n_products),
        "product_photos_qty":          rng.integers(1, 8, n_products),
        "product_weight_g":            rng.integers(100, 30000, n_products).astype(float),
        "product_length_cm":           rng.integers(10, 80, n_products).astype(float),
        "product_height_cm":           rng.integers(5, 40, n_products).astype(float),
        "product_width_cm":            rng.integers(10, 80, n_products).astype(float),
    })
    # Introduce ~3% nulls in weight
    null_mask = rng.random(n_products) < 0.03
    products_df.loc[null_mask, "product_weight_g"] = None
    products_df.to_csv(os.path.join(RAW_DIR, "olist_products_dataset.csv"), index=False)
    print(f"✓  products         {len(products_df):>5} rows")

    # ── Orders ────────────────────────────────────────────────────────────────
    order_ids    = [uid() for _ in range(n_orders)]
    cust_sample  = rng.choice(customer_ids, n_orders)
    status_sample= rng.choice(STATUSES, n_orders)
    purchase_dts = [rand_date(base, 730) for _ in range(n_orders)]

    delivered_dts = []
    estimated_dts = []
    approved_dts  = []
    carrier_dts   = []

    for i, (pdt, status) in enumerate(zip(purchase_dts, status_sample)):
        approved = pdt + timedelta(hours=random.randint(1, 48))
        carrier  = approved + timedelta(days=random.randint(1, 5))
        est_days = random.randint(7, 30)
        estimated = pdt + timedelta(days=est_days)
        if status == "delivered":
            actual_days = random.randint(5, est_days + 5)  # some late
            delivered = pdt + timedelta(days=actual_days)
        else:
            delivered = None
        approved_dts.append(approved)
        carrier_dts.append(carrier if status not in ("canceled",) else None)
        estimated_dts.append(estimated)
        delivered_dts.append(delivered)

    orders_df = pd.DataFrame({
        "order_id":                      order_ids,
        "customer_id":                   cust_sample,
        "order_status":                  status_sample,
        "order_purchase_timestamp":      [d.strftime("%Y-%m-%d %H:%M:%S") for d in purchase_dts],
        "order_approved_at":             [d.strftime("%Y-%m-%d %H:%M:%S") if d else None for d in approved_dts],
        "order_delivered_carrier_date":  [d.strftime("%Y-%m-%d %H:%M:%S") if d else None for d in carrier_dts],
        "order_delivered_customer_date": [d.strftime("%Y-%m-%d %H:%M:%S") if d else None for d in delivered_dts],
        "order_estimated_delivery_date": [d.strftime("%Y-%m-%d %H:%M:%S") for d in estimated_dts],
    })
    orders_df.to_csv(os.path.join(RAW_DIR, "olist_orders_dataset.csv"), index=False)
    print(f"✓  orders           {len(orders_df):>5} rows")

    # ── Order Items ───────────────────────────────────────────────────────────
    items_rows = []
    for order_id in order_ids:
        n_items = rng.integers(1, 4)
        for item_num in range(1, n_items + 1):
            items_rows.append({
                "order_id":           order_id,
                "order_item_id":      item_num,
                "product_id":         rng.choice(product_ids),
                "seller_id":          rng.choice(seller_ids),
                "shipping_limit_date": rand_date(base, 730).strftime("%Y-%m-%d %H:%M:%S"),
                "price":              round(float(rng.uniform(10, 800)), 2),
                "freight_value":      round(float(rng.uniform(5, 80)), 2),
            })
    items_df = pd.DataFrame(items_rows)
    items_df.to_csv(os.path.join(RAW_DIR, "olist_order_items_dataset.csv"), index=False)
    print(f"✓  order_items      {len(items_df):>5} rows")

    # ── Payments ──────────────────────────────────────────────────────────────
    pay_rows = []
    for order_id in order_ids:
        pay_rows.append({
            "order_id":               order_id,
            "payment_sequential":     1,
            "payment_type":           rng.choice(PAYMENT_TYPES),
            "payment_installments":   int(rng.integers(1, 12)),
            "payment_value":          round(float(rng.uniform(20, 900)), 2),
        })
    payments_df = pd.DataFrame(pay_rows)
    payments_df.to_csv(os.path.join(RAW_DIR, "olist_order_payments_dataset.csv"), index=False)
    print(f"✓  payments         {len(payments_df):>5} rows")

    # ── Reviews ───────────────────────────────────────────────────────────────
    rev_rows = []
    for order_id, pdt in zip(order_ids, purchase_dts):
        if rng.random() < 0.75:   # ~75% of orders have a review
            creation = pdt + timedelta(days=random.randint(2, 15))
            rev_rows.append({
                "review_id":               uid(),
                "order_id":                order_id,
                "review_score":            int(rng.integers(1, 6)),
                "review_comment_title":    "",
                "review_comment_message":  "",
                "review_creation_date":    creation.strftime("%Y-%m-%d %H:%M:%S"),
                "review_answer_timestamp": (creation + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            })
    reviews_df = pd.DataFrame(rev_rows)
    reviews_df.to_csv(os.path.join(RAW_DIR, "olist_order_reviews_dataset.csv"), index=False)
    print(f"✓  reviews          {len(reviews_df):>5} rows")

    print(f"\n✓  All sample CSVs written to: {RAW_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate sample Olist-schema data")
    parser.add_argument("--rows", type=int, default=500,
                        help="Number of orders to generate (default: 500)")
    args = parser.parse_args()
    generate(args.rows)
