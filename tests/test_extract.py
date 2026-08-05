"""
Tests – Extract Layer
Covers: empty CSV, missing files, wrong columns, encoding.
"""

import os
import pytest
import pandas as pd

from extract.extract_orders import extract_orders
from extract.extract_customers import extract_customers


# ── Helpers ────────────────────────────────────────────────────────────────────

def _write_csv(tmp_path, filename: str, content: str) -> str:
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return str(p)


# ── extract_orders ─────────────────────────────────────────────────────────────

class TestExtractOrders:

    def test_missing_file_raises(self):
        """FileNotFoundError is raised when file does not exist."""
        with pytest.raises(FileNotFoundError):
            extract_orders(filepath="/nonexistent/path/orders.csv")

    def test_empty_csv_returns_empty_df(self, tmp_path):
        """An empty CSV (headers only) returns an empty DataFrame."""
        path = _write_csv(tmp_path, "orders.csv", "order_id,customer_id,order_status\n")
        df = extract_orders(filepath=path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_valid_csv_loads(self, tmp_path):
        """A valid CSV is loaded and returns the correct number of rows."""
        content = (
            "order_id,customer_id,order_status\n"
            "O1,C1,delivered\n"
            "O2,C2,shipped\n"
        )
        path = _write_csv(tmp_path, "orders.csv", content)
        df = extract_orders(filepath=path)
        assert len(df) == 2
        assert "order_id" in df.columns

    def test_wrong_columns_still_loads(self, tmp_path):
        """CSV with unexpected columns loads without error."""
        path = _write_csv(tmp_path, "orders.csv", "col_a,col_b\n1,2\n")
        df = extract_orders(filepath=path)
        assert "col_a" in df.columns

    def test_latin1_encoding(self, tmp_path):
        """Latin-1 encoded file is loaded via fallback encoding."""
        p = tmp_path / "orders.csv"
        p.write_bytes("order_id,customer_id\nO1,C\xe9sar\n".encode("latin-1"))
        df = extract_orders(filepath=str(p))
        assert len(df) == 1


# ── extract_customers ──────────────────────────────────────────────────────────

class TestExtractCustomers:

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            extract_customers(filepath="/nonexistent/customers.csv")

    def test_valid_csv_loads(self, tmp_path):
        content = (
            "customer_id,customer_unique_id,customer_state\n"
            "C1,U1,SP\n"
            "C2,U2,RJ\n"
        )
        path = _write_csv(tmp_path, "customers.csv", content)
        df = extract_customers(filepath=path)
        assert len(df) == 2
        assert "customer_id" in df.columns
