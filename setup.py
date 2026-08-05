"""
setup.py
========
One-command full project setup. Runs all steps in order:

  1. Create .env from defaults
  2. Download Olist dataset (Kaggle) OR generate sample data
  3. Run the pipeline (extract → validate → clean → transform)
  4. Optionally load into PostgreSQL
  5. Optionally backup to S3
  6. Print next-step instructions

Usage:
    python setup.py                        # full auto setup
    python setup.py --use-sample-data      # skip Kaggle, use generated data
    python setup.py --kaggle-user U --kaggle-key K
    python setup.py --with-db              # also load into PostgreSQL
    python setup.py --with-s3              # also backup to S3
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def run_script(script: str, args: list[str] = []) -> None:
    """Run a project Python script and exit on failure."""
    cmd = [sys.executable, os.path.join(PROJECT_ROOT, script)] + args
    print(f"\n{'=' * 60}")
    print(f"  Running: {script}")
    print(f"{'=' * 60}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"\n✗  {script} failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="Sales ETL Pipeline — Full Setup")
    parser.add_argument("--use-sample-data",  action="store_true",
                        help="Generate sample data instead of downloading from Kaggle")
    parser.add_argument("--sample-rows",      type=int, default=1000,
                        help="Number of sample orders to generate (default: 1000)")
    parser.add_argument("--kaggle-user",      help="Kaggle username")
    parser.add_argument("--kaggle-key",       help="Kaggle API key")
    parser.add_argument("--with-db",          action="store_true",
                        help="Load data into PostgreSQL after pipeline")
    parser.add_argument("--with-s3",          action="store_true",
                        help="Backup data to AWS S3 after pipeline")
    parser.add_argument("--non-interactive",  action="store_true",
                        help="Use default .env values without prompting")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  Sales ETL Pipeline — Automated Setup")
    print("=" * 60)

    # ── Step 1: Create .env ────────────────────────────────────────────────
    print("\n[1/4]  Creating .env file...")
    env_args = ["--non-interactive"] if args.non_interactive else []
    run_script("setup_env.py", env_args)

    # ── Step 2: Get data ──────────────────────────────────────────────────
    print("\n[2/4]  Preparing data...")
    if args.use_sample_data:
        run_script("generate_sample_data.py", ["--rows", str(args.sample_rows)])
    else:
        kaggle_args = []
        if args.kaggle_user:
            kaggle_args += ["--username", args.kaggle_user]
        if args.kaggle_key:
            kaggle_args += ["--key", args.kaggle_key]
        run_script("setup_kaggle.py", kaggle_args)

    # ── Step 3: Run pipeline ──────────────────────────────────────────────
    print("\n[3/4]  Running ETL pipeline...")
    pipeline_args: list[str] = []
    if not args.with_db:
        pipeline_args.append("--skip-db")
    if not args.with_s3:
        pipeline_args.append("--skip-s3")
    run_script("run_pipeline.py", pipeline_args)

    # ── Step 4: Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  ✓  Setup complete!")
    print("=" * 60)

    cleaned_dir    = os.path.join(PROJECT_ROOT, "data", "cleaned")
    transformed_dir = os.path.join(PROJECT_ROOT, "data", "transformed")

    if os.path.exists(cleaned_dir):
        files = os.listdir(cleaned_dir)
        print(f"\n  Cleaned files    ({len(files)} files in data/cleaned/):")
        for f in sorted(files):
            size = os.path.getsize(os.path.join(cleaned_dir, f)) // 1024
            print(f"    {f:45s}  {size:>5} KB")

    if os.path.exists(transformed_dir):
        files = os.listdir(transformed_dir)
        print(f"\n  Transformed files ({len(files)} files in data/transformed/):")
        for f in sorted(files):
            size = os.path.getsize(os.path.join(transformed_dir, f)) // 1024
            print(f"    {f:45s}  {size:>5} KB")

    print("\n" + "=" * 60)
    print("  NEXT STEPS")
    print("=" * 60)
    if not args.with_db:
        print("\n  Load into PostgreSQL:")
        print("    Option A — Docker (recommended):")
        print("      python start_docker.py")
        print("\n    Option B — Local PostgreSQL:")
        print("      python run_pipeline.py --skip-s3")

    if not args.with_s3:
        print("\n  Backup to AWS S3:")
        print("    1. Edit .env — add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("    2. python run_pipeline.py --skip-db")

    print("\n  Power BI Dashboard:")
    print("    See dashboard/powerbi_guide.md for step-by-step instructions")
    print("    Or import CSVs directly from data/transformed/")

    print("\n  Run tests:")
    print("    python -m pytest tests/ -v")

    print("\n  Use real Kaggle data (100K+ rows):")
    print("    python setup_kaggle.py --username YOUR_NAME --key YOUR_KEY")
    print("    python run_pipeline.py --skip-s3 --skip-db")
    print()


if __name__ == "__main__":
    main()
