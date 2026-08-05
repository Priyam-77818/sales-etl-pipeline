"""
Tests – Validation Layer
Covers: missing values, duplicates, invalid dates, null customer IDs.
"""

import pytest
import pandas as pd

from validation.validate_orders import validate_orders
from validation.validate_customers import validate_customers


class TestValidateOrders:

    def _base_df(self):
        return pd.DataFrame({
            "order_id": ["O1", "O2"],
            "customer_id": ["C1", "C2"],
            "order_status": ["delivered", "shipped"],
            "order_purchase_timestamp": ["2018-01-01 10:00:00", "2018-01-02 11:00:00"],
            "order_approved_at": ["2018-01-01 12:00:00", "2018-01-02 13:00:00"],
            "order_delivered_carrier_date": ["2018-01-05", "2018-01-06"],
            "order_delivered_customer_date": ["2018-01-10", "2018-01-11"],
            "order_estimated_delivery_date": ["2018-01-20", "2018-01-21"],
        })

    def test_clean_df_returns_pass(self, tmp_path, monkeypatch):
        """A clean DataFrame should return status PASS."""
        import validation.validate_orders as vo
        monkeypatch.setattr(vo, "CLEANED_DIR", str(tmp_path))
        report = validate_orders(self._base_df())
        assert report["status"] == "PASS"

    def test_duplicate_order_ids_detected(self, tmp_path, monkeypatch):
        import validation.validate_orders as vo
        monkeypatch.setattr(vo, "CLEANED_DIR", str(tmp_path))
        df = self._base_df()
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        report = validate_orders(df)
        assert report["duplicate_order_ids"] >= 1

    def test_null_customer_ids_detected(self, tmp_path, monkeypatch):
        import validation.validate_orders as vo
        monkeypatch.setattr(vo, "CLEANED_DIR", str(tmp_path))
        df = self._base_df()
        df.loc[0, "customer_id"] = None
        report = validate_orders(df)
        assert report["null_customer_ids"] >= 1

    def test_invalid_date_format_detected(self, tmp_path, monkeypatch):
        import validation.validate_orders as vo
        monkeypatch.setattr(vo, "CLEANED_DIR", str(tmp_path))
        df = self._base_df()
        df.loc[0, "order_purchase_timestamp"] = "NOT_A_DATE"
        report = validate_orders(df)
        assert report["date_format_issues"]["order_purchase_timestamp"] >= 1

    def test_report_csv_created(self, tmp_path, monkeypatch):
        import validation.validate_orders as vo
        monkeypatch.setattr(vo, "CLEANED_DIR", str(tmp_path))
        validate_orders(self._base_df())
        assert (tmp_path / "validation_report_orders.csv").exists()


class TestValidateCustomers:

    def _base_df(self):
        return pd.DataFrame({
            "customer_id": ["C1", "C2"],
            "customer_unique_id": ["U1", "U2"],
            "customer_zip_code_prefix": ["01001", "01002"],
            "customer_city": ["sao paulo", "rio de janeiro"],
            "customer_state": ["SP", "RJ"],
        })

    def test_clean_df_returns_pass(self, tmp_path, monkeypatch):
        import validation.validate_customers as vc
        monkeypatch.setattr(vc, "CLEANED_DIR", str(tmp_path))
        report = validate_customers(self._base_df())
        assert report["status"] == "PASS"

    def test_duplicate_customer_ids_detected(self, tmp_path, monkeypatch):
        import validation.validate_customers as vc
        monkeypatch.setattr(vc, "CLEANED_DIR", str(tmp_path))
        df = self._base_df()
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        report = validate_customers(df)
        assert report["duplicate_customer_ids"] >= 1
