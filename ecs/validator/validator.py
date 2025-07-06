import boto3
import os
import pandas as pd
import io
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BUCKET = os.getenv("BUCKET")

s3 = boto3.client("s3")

# Expected schema definitions
EXPECTED_SCHEMAS = {
    "orders": ["order_id", "user_id", "created_at", "status", "num_of_item"],
    "order_items": ["order_id", "product_id", "created_at", "sale_price", "status"]
}



def list_csv_files(prefix):
    """List all CSV files under the prefix."""
    paginator = s3.get_paginator("list_objects_v2")
    files = []
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".csv"):
                files.append(obj["Key"])
    return files

def validate_columns(df, expected_columns):
    return set(expected_columns).issubset(set(df.columns))

def copy_and_delete(src_key, dest_key):
    s3.copy_object(Bucket=BUCKET, CopySource={"Bucket": BUCKET, "Key": src_key}, Key=dest_key)
    s3.delete_object(Bucket=BUCKET, Key=src_key)

def save_manifest(manifest, date_str):
    manifest_key = f"validated/manifests/batch_{date_str}.json"
    s3.put_object(
        Bucket=BUCKET,
        Key=manifest_key,
        Body=json.dumps(manifest, indent=2).encode("utf-8")
    )
    print(f" Manifest saved: s3://{BUCKET}/{manifest_key}")

def handler():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    manifest = {"orders": [], "order_items": []}

    for file_type, expected_columns in EXPECTED_SCHEMAS.items():
        incoming_prefix = f"incoming/{file_type}/"
        files = list_csv_files(incoming_prefix)

        print(f" Found {len(files)} file(s) in {incoming_prefix}")

        for key in files:
            obj = s3.get_object(Bucket=BUCKET, Key=key)
            body = obj["Body"].read().decode("utf-8")
            df = pd.read_csv(io.StringIO(body))

            filename = os.path.basename(key)
            validated_key = f"validated/{file_type}/dt={today}/{filename}"
            failed_key = f"failed/{file_type}/{filename}"
            archive_key = f"archive/{file_type}/dt={today}/{filename}"

            if df.empty:
                print(f" Empty file skipped: {key}")
                continue

            try:
                if validate_columns(df, expected_columns):
                    # Valid file: move to validated
                    copy_and_delete(key, validated_key)
                    manifest[file_type].append(validated_key)
                    print(f" Validated: {key} ➝ {validated_key}")
                    # Archive validated copy
                    s3.copy_object(Bucket=BUCKET, CopySource={"Bucket": BUCKET, "Key": validated_key}, Key=archive_key)
                    print(f" Archived validated to: {archive_key}")
                else:
                    # Invalid file: move to failed
                    copy_and_delete(key, failed_key)
                    print(f" Invalid schema: {key} ➝ {failed_key}")
                    # Archive failed copy
                    s3.copy_object(Bucket=BUCKET, CopySource={"Bucket": BUCKET, "Key": failed_key}, Key=archive_key)
                    print(f" Archived failed to: {archive_key}")
            except Exception as e:
                print(f" Error processing {key}: {e}")

    if manifest["orders"] or manifest["order_items"]:
        save_manifest(manifest, today)
    else:
        print(" No validated files; no manifest generated.")

    print(" Validation complete.")

if __name__ == "__main__":
    handler()
