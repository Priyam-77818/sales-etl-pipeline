"""
setup_kaggle.py
===============
Step 1 — Download the Olist dataset from Kaggle automatically.

HOW TO GET YOUR KAGGLE API KEY:
  1. Go to https://www.kaggle.com  →  Your profile  →  Settings
  2. Scroll to "API" section  →  click "Create New Token"
  3. This downloads  kaggle.json  containing your username + key
  4. Run this script — it will ask you to paste those values,
     then save them to  C:\\Users\\<you>\\.kaggle\\kaggle.json
     and download the dataset into  data/raw/

Usage:
    python setup_kaggle.py
    python setup_kaggle.py --username YOUR_NAME --key YOUR_KEY
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
import subprocess

KAGGLE_DIR  = os.path.join(os.path.expanduser("~"), ".kaggle")
KAGGLE_JSON = os.path.join(KAGGLE_DIR, "kaggle.json")
RAW_DIR     = os.path.join(os.path.dirname(__file__), "data", "raw")
DATASET     = "olistbr/brazilian-ecommerce"

EXPECTED_FILES = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_sellers_dataset.csv",
]


def save_credentials(username: str, key: str) -> None:
    os.makedirs(KAGGLE_DIR, exist_ok=True)
    with open(KAGGLE_JSON, "w") as f:
        json.dump({"username": username, "key": key}, f)
    # Kaggle API requires 600 permissions on non-Windows
    if os.name != "nt":
        os.chmod(KAGGLE_JSON, 0o600)
    print(f"✓  Credentials saved to {KAGGLE_JSON}")


def credentials_exist() -> bool:
    return os.path.exists(KAGGLE_JSON)


def all_csvs_present() -> bool:
    return all(
        os.path.exists(os.path.join(RAW_DIR, f))
        for f in EXPECTED_FILES
    )


def download_dataset() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    print(f"\nDownloading dataset: {DATASET}")
    print(f"Destination: {RAW_DIR}\n")

    result = subprocess.run(
        [
            sys.executable, "-m", "kaggle",
            "datasets", "download",
            "-d", DATASET,
            "-p", RAW_DIR,
            "--unzip",
            "--force",
        ],
        capture_output=False,
    )

    if result.returncode != 0:
        print("\n✗  Download failed.")
        print("   Make sure your Kaggle credentials are correct and you have")
        print("   accepted the dataset rules at:")
        print(f"   https://www.kaggle.com/datasets/{DATASET}")
        sys.exit(1)

    # Verify
    missing = [f for f in EXPECTED_FILES if not os.path.exists(os.path.join(RAW_DIR, f))]
    if missing:
        print(f"\n⚠  Downloaded but these files are missing: {missing}")
    else:
        print("\n✓  All 7 CSV files downloaded successfully into data/raw/")
        for f in EXPECTED_FILES:
            size = os.path.getsize(os.path.join(RAW_DIR, f)) // 1024
            print(f"   {f:50s}  {size:>6} KB")


def main():
    parser = argparse.ArgumentParser(description="Download Olist dataset from Kaggle")
    parser.add_argument("--username", help="Kaggle username")
    parser.add_argument("--key",      help="Kaggle API key")
    args = parser.parse_args()

    # ── Check if already done ────────────────────────────────────────────────
    if all_csvs_present():
        print("✓  All CSV files already present in data/raw/  — nothing to download.")
        return

    # ── Get credentials ──────────────────────────────────────────────────────
    if not credentials_exist():
        if args.username and args.key:
            save_credentials(args.username, args.key)
        else:
            print("=" * 60)
            print("  Kaggle API credentials not found.")
            print("  Get them from: https://www.kaggle.com/settings")
            print("  (Profile → API → Create New Token → kaggle.json)")
            print("=" * 60)
            username = input("\nEnter your Kaggle username: ").strip()
            key      = input("Enter your Kaggle API key  : ").strip()
            if not username or not key:
                print("✗  Username and key are required.")
                sys.exit(1)
            save_credentials(username, key)
    else:
        print(f"✓  Using existing credentials: {KAGGLE_JSON}")

    download_dataset()


if __name__ == "__main__":
    main()
