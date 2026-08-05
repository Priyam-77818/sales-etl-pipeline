"""
AWS S3 Backup
Uploads processed CSVs and logs to the configured S3 bucket.

Folder structure in S3:
  s3://<bucket>/raw/         ← raw CSVs (optional)
  s3://<bucket>/cleaned/     ← cleaned CSVs
  s3://<bucket>/transformed/ ← star-schema CSVs
  s3://<bucket>/reports/     ← validation reports
  s3://<bucket>/logs/        ← pipeline logs
"""

import os
import glob
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "logs", "pipeline.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("s3_backup")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_s3_client(
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    region_name: Optional[str] = None,
):
    """Create and return a boto3 S3 client."""
    return boto3.client(
        "s3",
        aws_access_key_id     = aws_access_key_id     or os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name           = region_name            or os.getenv("AWS_REGION", "us-east-1"),
    )


def upload_file(s3_client, local_path: str, bucket: str, s3_key: str) -> bool:
    """
    Upload a single file to S3.

    Returns True on success, False on failure.
    """
    try:
        s3_client.upload_file(local_path, bucket, s3_key)
        logger.info("Uploaded: %s → s3://%s/%s", local_path, bucket, s3_key)
        return True
    except FileNotFoundError:
        logger.error("Local file not found: %s", local_path)
        return False
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        return False
    except ClientError as exc:
        logger.error("S3 upload failed for %s: %s", local_path, exc)
        return False


def backup_all(bucket: Optional[str] = None) -> dict:
    """
    Upload all cleaned, transformed, report, and log files to S3.

    Parameters
    ----------
    bucket : str, optional
        S3 bucket name. Falls back to S3_BUCKET env var or 'sales-etl-pipeline'.

    Returns
    -------
    dict  {"uploaded": int, "failed": int}
    """
    bucket = bucket or os.getenv("S3_BUCKET", "sales-etl-pipeline")
    s3 = get_s3_client()

    upload_map = {
        "cleaned":     os.path.join(BASE_DIR, "data", "cleaned", "*.csv"),
        "transformed": os.path.join(BASE_DIR, "data", "transformed", "*.csv"),
        "reports":     os.path.join(BASE_DIR, "data", "cleaned", "validation_report_*.csv"),
        "logs":        os.path.join(BASE_DIR, "logs", "*.log"),
    }

    uploaded, failed = 0, 0

    for s3_prefix, pattern in upload_map.items():
        for local_path in glob.glob(pattern):
            key = f"{s3_prefix}/{os.path.basename(local_path)}"
            if upload_file(s3, local_path, bucket, key):
                uploaded += 1
            else:
                failed += 1

    logger.info("S3 backup complete — uploaded: %d, failed: %d", uploaded, failed)
    return {"uploaded": uploaded, "failed": failed}


def create_bucket_if_not_exists(bucket: str, region: str = "us-east-1") -> None:
    """Create the S3 bucket if it doesn't already exist."""
    s3 = get_s3_client()
    try:
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket)
        else:
            s3.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        logger.info("S3 bucket created: %s", bucket)
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        if error_code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            logger.info("S3 bucket already exists: %s", bucket)
        else:
            logger.error("Failed to create bucket %s: %s", bucket, exc)
            raise


if __name__ == "__main__":
    result = backup_all()
    print(result)
