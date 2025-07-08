import boto3
import os
import pandas as pd
import io
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# ---------------------------------------------
# Setup Logging
# ---------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------------------------------------
# Load environment variables
# ---------------------------------------------
load_dotenv()
BUCKET = os.getenv("BUCKET")

# Initialize S3 client
s3 = boto3.client("s3")

# ---------------------------------------------
# Define expected schema for each file type
# ---------------------------------------------
EXPECTED_SCHEMAS = {
    "orders": ["order_id", "user_id", "created_at", "status", "num_of_item"],
    "order_items": ["order_id", "product_id", "created_at", "sale_price", "status"]
}

# ---------------------------------------------
# Utility Functions
# ---------------------------------------------

def list_csv_files(prefix):
    """
    List all CSV files under a given S3 prefix.
    """
    paginator = s3.get_paginator("list_objects_v2")
    files = []
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".csv"):
                files.append(obj["Key"])
    return files

def validate_columns(df, expected_columns):
    """
    Check whether the dataframe contains the expected columns.
    """
    return set(expected_columns).issubset(set(df.columns))

def copy_and_delete(src_key, dest_key):
    """
    Copy an object to a new key and delete the original.
    """
    s3.copy_object(Bucket=BUCKET, CopySource={"Bucket": BUCKET, "Key": src_key}, Key=dest_key)
    s3.delete_object(Bucket=BUCKET, Key=src_key)

def save_manifest(manifest, date_str):
    """
    Save a manifest JSON file containing validated file paths.
    """
    manifest_key = f"validated/manifests/batch_{date_str}.json"
    s3.put_object(
        Bucket=BUCKET,
        Key=manifest_key,
        Body=json.dumps(manifest, indent=2).encode("utf-8")
    )
    logger.info(f"Manifest saved: s3://{BUCKET}/{manifest_key}")

# ---------------------------------------------
# Main handler function
# ---------------------------------------------

def handler():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    manifest = {"orders": [], "order_items": []}

    logger.info("Starting file validation process.")

    for file_type, expected_columns in EXPECTED_SCHEMAS.items():
        incoming_prefix = f"incoming/{file_type}/"
        files = list_csv_files(incoming_prefix)

        logger.info(f"Found {len(files)} file(s) in '{incoming_prefix}'.")

        for key in files:
            try:
                # Read file content into DataFrame
                obj = s3.get_object(Bucket=BUCKET, Key=key)
                body = obj["Body"].read().decode("utf-8")
                df = pd.read_csv(io.StringIO(body))

                filename = os.path.basename(key)
                validated_key = f"validated/{file_type}/dt={today}/{filename}"
                failed_key = f"failed/{file_type}/{filename}"
                archive_key = f"archive/{file_type}/dt={today}/{filename}"

                if df.empty:
                    logger.warning(f"Empty file skipped: {key}")
                    continue

                if validate_columns(df, expected_columns):
                    # Move to validated and archive it
                    copy_and_delete(key, validated_key)
                    s3.copy_object(Bucket=BUCKET, CopySource={"Bucket": BUCKET, "Key": validated_key}, Key=archive_key)
                    manifest[file_type].append(validated_key)

                    logger.info(f"Validated: {key} ➝ {validated_key}")
                    logger.info(f"Archived validated file: {archive_key}")
                else:
                    # Move to failed and archive it
                    copy_and_delete(key, failed_key)
                    s3.copy_object(Bucket=BUCKET, CopySource={"Bucket": BUCKET, "Key": failed_key}, Key=archive_key)

                    logger.warning(f"Invalid schema: {key} ➝ {failed_key}")
                    logger.info(f"Archived failed file: {archive_key}")

            except Exception as e:
                logger.error(f"Error processing {key}: {e}")

    if manifest["orders"] or manifest["order_items"]:
        save_manifest(manifest, today)
    else:
        logger.info("No validated files found; manifest not generated.")

    logger.info("Validation process completed.")

# ---------------------------------------------
# Entry point
# ---------------------------------------------
if __name__ == "__main__":
    handler()
