"""
Tests – Transform Layer
Covers: cleaning, feature engineering, star schema builds.
"""

import pytest
import pandas as pd
import numpy as np

from transform.clean_orders import (
    clean_orders, clean_customers, clean_products, clean_items,
)
from transform.feature_engineering import build_order_features
from transform.star_schema import (
    build_dim_customer, build_dim_product, build_dim_date, build_fact_sales,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_orders():
    return pd.DataFrame({
        "order_id": ["O1", "O2", "O1"],  # duplicate
        "customer_id": ["C1", "C2", "C1"],
        "order_status": ["DELIVERED", "shipped", "DELIVERED"],
        "order_purchase_timestamp": ["2018-01-01 10:00:00", "2018-02-15 08:30:00", "2018-01-01 10:00:00"],
        "order_approved_at": ["2018-01-01 12:00:00", None, "2018-01-01 12:00:00"],
        "order_delivered_carrier_date": [None, "2018-02-18", None],
        "order_delivered_customer_date": ["2018-01-10", "2018-02-20", "2018-01-10"],
        "order_estimated_delivery_date": ["2018-01-15", "2018-02-25", "2018-01-15"],
    })


@pytest.fixture
def sample_customers():
    return pd.DataFrame({
        "customer_id": ["C1", "C2"],
        "customer_unique_id": ["U1", "U2"],
        "customer_zip_code_prefix": [1001, 2002],
        "customer_city": ["São Paulo", "Rio de Janeiro"],
        "customer_state": ["SP", "RJ"],
    })


@pytest.fixture
def sample_items():
    return pd.DataFrame({
        "order_id": ["O1", "O2"],
        "order_item_id": [1, 1],
        "product_id": ["P1", "P2"],
        "seller_id": ["S1", "S2"],
        "price": [100.0, 250.0],
        "freight_value": [10.0, 20.0],
        "shipping_limit_date": ["2018-01-05", "2018-02-18"],
    })


@pytest.fixture
def sample_payments():
    return pd.DataFrame({
        "order_id": ["O1", "O2"],
        "payment_sequential": [1, 1],
        "payment_type": ["credit_card", "boleto"],
        "payment_installments": [1, 1],
        "payment_value": [110.0, 270.0],
    })


@pytest.fixture
def sample_reviews():
    return pd.DataFrame({
        "review_id": ["R1", "R2"],
        "order_id": ["O1", "O2"],
        "review_score": [5, 3],
        "review_creation_date": ["2018-01-11", "2018-02-21"],
        "review_answer_timestamp": ["2018-01-12", "2018-02-22"],
    })


@pytest.fixture
def sample_products():
    return pd.DataFrame({
        "product_id": ["P1", "P2"],
        "product_category_name": ["eletronicos", "cama_mesa_banho"],
        "product_name_lenght": [20, 30],
        "product_description_lenght": [100, 200],
        "product_photos_qty": [3, 5],
        "product_weight_g": [500.0, np.nan],
        "product_length_cm": [20.0, 30.0],
        "product_height_cm": [10.0, 15.0],
        "product_width_cm": [15.0, 20.0],
    })


# ── clean_orders ───────────────────────────────────────────────────────────────

class TestCleanOrders:

    def test_removes_duplicates(self, sample_orders, tmp_path, monkeypatch):
        import transform.clean_orders as co
        monkeypatch.setattr(co, "CLEANED_DIR", str(tmp_path))
        cleaned = clean_orders(sample_orders)
        assert cleaned["order_id"].duplicated().sum() == 0

    def test_dates_converted(self, sample_orders, tmp_path, monkeypatch):
        import transform.clean_orders as co
        monkeypatch.setattr(co, "CLEANED_DIR", str(tmp_path))
        cleaned = clean_orders(sample_orders)
        assert pd.api.types.is_datetime64_any_dtype(cleaned["order_purchase_timestamp"])

    def test_strings_lowercased(self, sample_orders, tmp_path, monkeypatch):
        import transform.clean_orders as co
        monkeypatch.setattr(co, "CLEANED_DIR", str(tmp_path))
        cleaned = clean_orders(sample_orders)
        assert cleaned["order_status"].str.islower().all()

    def test_csv_saved(self, sample_orders, tmp_path, monkeypatch):
        import transform.clean_orders as co
        monkeypatch.setattr(co, "CLEANED_DIR", str(tmp_path))
        clean_orders(sample_orders)
        assert (tmp_path / "orders_cleaned.csv").exists()


# ── clean_items ────────────────────────────────────────────────────────────────

class TestCleanItems:

    def test_negative_price_removed(self, tmp_path, monkeypatch):
        import transform.clean_orders as co
        monkeypatch.setattr(co, "CLEANED_DIR", str(tmp_path))
        df = pd.DataFrame({
            "order_id": ["O1", "O2"],
            "order_item_id": [1, 1],
            "product_id": ["P1", "P2"],
            "seller_id": ["S1", "S2"],
            "price": [-10.0, 50.0],
            "freight_value": [5.0, 5.0],
        })
        cleaned = clean_items(df)
        assert (cleaned["price"] > 0).all()


# ── Feature Engineering ────────────────────────────────────────────────────────

class TestFeatureEngineering:

    def test_time_features_added(self, sample_orders, sample_items, sample_customers, tmp_path, monkeypatch):
        import transform.feature_engineering as fe
        monkeypatch.setattr(fe, "TRANSFORMED_DIR", str(tmp_path))
        import transform.clean_orders as co
        monkeypatch.setattr(co, "CLEANED_DIR", str(tmp_path))

        orders = clean_orders(sample_orders)
        result = build_order_features(orders, sample_items, sample_customers)
        assert "month" in result.columns
        assert "year" in result.columns
        assert "quarter" in result.columns

    def test_clv_computed(self, sample_orders, sample_items, sample_customers, tmp_path, monkeypatch):
        import transform.feature_engineering as fe
        monkeypatch.setattr(fe, "TRANSFORMED_DIR", str(tmp_path))
        import transform.clean_orders as co
        monkeypatch.setattr(co, "CLEANED_DIR", str(tmp_path))

        orders = clean_orders(sample_orders)
        result = build_order_features(orders, sample_items, sample_customers)
        assert "customer_lifetime_value" in result.columns


# ── Star Schema ────────────────────────────────────────────────────────────────

class TestStarSchema:

    def test_dim_customer_unique_ids(self, sample_customers, tmp_path, monkeypatch):
        import transform.star_schema as ss
        monkeypatch.setattr(ss, "TRANSFORMED_DIR", str(tmp_path))
        dim = build_dim_customer(sample_customers)
        assert dim["customer_id"].duplicated().sum() == 0

    def test_dim_product_renames_typo_columns(self, sample_products, tmp_path, monkeypatch):
        import transform.star_schema as ss
        monkeypatch.setattr(ss, "TRANSFORMED_DIR", str(tmp_path))
        dim = build_dim_product(sample_products)
        assert "product_name_length" in dim.columns

    def test_dim_date_has_correct_columns(self, sample_orders, tmp_path, monkeypatch):
        import transform.star_schema as ss
        monkeypatch.setattr(ss, "TRANSFORMED_DIR", str(tmp_path))
        dim = build_dim_date(sample_orders)
        for col in ["date_id", "full_date", "year", "month", "quarter"]:
            assert col in dim.columns

    def test_fact_sales_has_surrogate_key(
        self, sample_orders, sample_items, sample_payments, sample_reviews,
        tmp_path, monkeypatch
    ):
        import transform.star_schema as ss
        monkeypatch.setattr(ss, "TRANSFORMED_DIR", str(tmp_path))
        fact = build_fact_sales(sample_orders, sample_items, sample_payments, sample_reviews)
        assert "fact_id" in fact.columns
        assert fact["fact_id"].is_unique
