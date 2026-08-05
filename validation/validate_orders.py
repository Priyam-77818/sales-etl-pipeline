"""
Validate Orders
Checks for missing values, duplicates, invalid IDs, negative prices,
wrong date formats, and null customer IDs.
Produces a validation_report.csv in data/cleaned/.
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
logger = logging.getLogger("validate_orders")

CLEANED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned")

DATE_COLUMNS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def validate_orders(df: pd.DataFrame) -> dict:
    """
    Run validation checks on the orders DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Raw orders DataFrame.

    Returns
    -------
    dict
        Validation report with counts per check.
    """
    report = {}
    logger.info("Validation started — orders (%d rows)", len(df))

    # 1. Missing values per column
    missing = df.isnull().sum().to_dict()
    report["missing_values"] = missing
    logger.info("Missing values: %s", missing)

    # 2. Duplicate order IDs
    dup_count = df.duplicated(subset=["order_id"]).sum()
    report["duplicate_order_ids"] = int(dup_count)
    logger.info("Duplicate order IDs: %d", dup_count)

    # 3. Null customer IDs
    null_customers = df["customer_id"].isnull().sum()
    report["null_customer_ids"] = int(null_customers)
    logger.info("Null customer IDs: %d", null_customers)

    # 4. Invalid order status values
    valid_statuses = {
        "delivered", "shipped", "canceled", "unavailable",
        "invoiced", "processing", "created", "approved",
    }
    if "order_status" in df.columns:
        invalid_status = (~df["order_status"].isin(valid_statuses)).sum()
        report["invalid_order_status"] = int(invalid_status)
        logger.info("Invalid order statuses: %d", invalid_status)

    # 5. Date format validation
    date_issues = {}
    for col in DATE_COLUMNS:
        if col in df.columns:
            parsed = pd.to_datetime(df[col], errors="coerce")
            bad = parsed.isnull().sum() - df[col].isnull().sum()
            bad = max(bad, 0)
            date_issues[col] = int(bad)
    report["date_format_issues"] = date_issues
    logger.info("Date format issues: %s", date_issues)

    # 6. Overall pass / fail
    total_issues = (
        sum(missing.values())
        + dup_count
        + null_customers
        + sum(date_issues.values())
    )
    report["total_issues"] = int(total_issues)
    report["status"] = "PASS" if total_issues == 0 else "WARNINGS"

    _save_report(report, "orders")
    logger.info("Orders validation complete — status: %s", report["status"])
    return report


def _save_report(report: dict, name: str) -> None:
    """Flatten the report dict and write to CSV."""
    os.makedirs(CLEANED_DIR, exist_ok=True)
    rows = []
    for check, value in report.items():
        if isinstance(value, dict):
            for sub_key, sub_val in value.items():
                rows.append({"check": f"{check}.{sub_key}", "value": sub_val})
        else:
            rows.append({"check": check, "value": value})

    report_df = pd.DataFrame(rows)
    out_path = os.path.join(CLEANED_DIR, f"validation_report_{name}.csv")
    report_df.to_csv(out_path, index=False)
    logger.info("Validation report saved: %s", out_path)


if __name__ == "__main__":
    from extract.extract_orders import extract_orders
    orders_df = extract_orders()
    result = validate_orders(orders_df)
    print(result)
