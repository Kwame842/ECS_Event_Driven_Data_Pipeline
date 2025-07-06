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