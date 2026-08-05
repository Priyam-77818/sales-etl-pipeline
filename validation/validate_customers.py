"""
Validate Customers
Checks for missing values, duplicates, invalid IDs, and null fields.
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
logger = logging.getLogger("validate_customers")

CLEANED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned")


def validate_customers(df: pd.DataFrame) -> dict:
    """
    Run validation checks on the customers DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Raw customers DataFrame.

    Returns
    -------
    dict
        Validation report with counts per check.
    """
    report = {}
    logger.info("Validation started — customers (%d rows)", len(df))

    # 1. Missing values
    missing = df.isnull().sum().to_dict()
    report["missing_values"] = missing
    logger.info("Missing values: %s", missing)

    # 2. Duplicate customer IDs
    dup_count = df.duplicated(subset=["customer_id"]).sum()
    report["duplicate_customer_ids"] = int(dup_count)
    logger.info("Duplicate customer IDs: %d", dup_count)

    # 3. Duplicate unique IDs
    if "customer_unique_id" in df.columns:
        dup_unique = df.duplicated(subset=["customer_unique_id"]).sum()
        report["duplicate_unique_ids"] = int(dup_unique)
        logger.info("Duplicate unique IDs: %d", dup_unique)

    # 4. Null zip codes
    if "customer_zip_code_prefix" in df.columns:
        null_zip = df["customer_zip_code_prefix"].isnull().sum()
        report["null_zip_codes"] = int(null_zip)
        logger.info("Null zip codes: %d", null_zip)

    # 5. Null state
    if "customer_state" in df.columns:
        null_state = df["customer_state"].isnull().sum()
        report["null_states"] = int(null_state)
        logger.info("Null states: %d", null_state)

    total_issues = (
        sum(missing.values())
        + dup_count
        + report.get("duplicate_unique_ids", 0)
        + report.get("null_zip_codes", 0)
        + report.get("null_states", 0)
    )
    report["total_issues"] = int(total_issues)
    report["status"] = "PASS" if total_issues == 0 else "WARNINGS"

    _save_report(report, "customers")
    logger.info("Customers validation complete — status: %s", report["status"])
    return report


def _save_report(report: dict, name: str) -> None:
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
    from extract.extract_customers import extract_customers
    df = extract_customers()
    result = validate_customers(df)
    print(result)
