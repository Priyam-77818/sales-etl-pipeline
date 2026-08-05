"""
prepare_deploy_data.py
Copies trimmed + compressed parquet files into dashboard/data/
for Streamlit Cloud deployment.
"""
import pandas as pd
import os

TRANSFORMED = "data/transformed"
OUT = "dashboard/data"
os.makedirs(OUT, exist_ok=True)

# fact_sales — keep only columns the dashboard uses
fact = pd.read_csv(f"{TRANSFORMED}/fact_sales.csv")
keep = [
    "order_id", "customer_id", "product_id", "seller_id", "date_id",
    "price", "freight_value", "payment_value", "payment_type",
    "review_score", "order_status", "delivery_time_days",
    "late_delivery", "revenue", "profit"
]
fact = fact[[c for c in keep if c in fact.columns]]

# Downcast numerics to save space
for col in ["price","freight_value","payment_value","revenue","profit"]:
    if col in fact.columns:
        fact[col] = pd.to_numeric(fact[col], errors="coerce").astype("float32")
for col in ["review_score","delivery_time_days","late_delivery"]:
    if col in fact.columns:
        fact[col] = pd.to_numeric(fact[col], errors="coerce").astype("Int16")

fact.to_parquet(f"{OUT}/fact_sales.parquet", index=False, compression="gzip")
size = os.path.getsize(f"{OUT}/fact_sales.parquet") // 1024
print(f"fact_sales : {len(fact):>6} rows  {size:>6} KB  (parquet+gzip)")

for name in ["dim_customer", "dim_product", "dim_seller", "dim_date"]:
    df = pd.read_csv(f"{TRANSFORMED}/{name}.csv")
    df.to_parquet(f"{OUT}/{name}.parquet", index=False, compression="gzip")
    size = os.path.getsize(f"{OUT}/{name}.parquet") // 1024
    print(f"{name:15}: {len(df):>6} rows  {size:>6} KB")

print("\nDone — parquet files written to dashboard/data/")
