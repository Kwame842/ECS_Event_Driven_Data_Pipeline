from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, sum as _sum, avg, countDistinct, max as _max, to_date, expr, when
)
from pyspark.sql.types import DecimalType, IntegerType
import boto3
import os
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv

# # Load environment variables
load_dotenv()

BUCKET = os.getenv("BUCKET")
ORDER_KPI_TABLE = os.getenv("ORDER_KPI_TABLE")
CATEGORY_KPI_TABLE = os.getenv("CATEGORY_KPI_TABLE")
PROCESSED_TABLE = os.getenv("PROCESSED_TABLE")
PRODUCTS_PREFIX = os.getenv("PRODUCTS_PREFIX", "static/")

# Initialize Spark
spark = (
    SparkSession.builder.appName("ECS-Order-KPI")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config(
        "spark.hadoop.fs.s3a.aws.credentials.provider",
        "com.amazonaws.auth.DefaultAWSCredentialsProviderChain",
    )
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "true")
    .config("spark.hadoop.fs.s3a.endpoint", "s3.amazonaws.com")
    .getOrCreate()
)

# AWS clients
dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")
order_table = dynamodb.Table(ORDER_KPI_TABLE)
category_table = dynamodb.Table(CATEGORY_KPI_TABLE)
processed_table = dynamodb.Table(PROCESSED_TABLE)


def list_new_files(prefix):
    paginator = s3_client.get_paginator("list_objects_v2")
    new_files = []
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".csv"):
                resp = processed_table.get_item(Key={"file_key": key})
                if "Item" not in resp:
                    new_files.append(key)
    return new_files

def get_latest_product_file(prefix):
    response = s3_client.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    files = [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".csv")]
    if not files:
        raise Exception(f"No product files found in {prefix}")
    return f"s3a://{BUCKET}/{sorted(files)[-1]}"

def mark_as_processed(key):
    processed_table.put_item(
        Item={
            "file_key": key,
            "processed_at": datetime.utcnow().isoformat(),
        }
    )

def archive_file(key):
    dest_key = key.replace("validated/", "processed/")
    s3_client.copy_object(
        Bucket=BUCKET,
        CopySource={"Bucket": BUCKET, "Key": key},
        Key=dest_key,
    )
    s3_client.delete_object(Bucket=BUCKET, Key=key)

def write_to_dynamodb(table, items):
    for item in items:
        for k, v in item.items():
            if isinstance(v, float):
                item[k] = Decimal(str(v))
        table.put_item(Item=item)

def handler():
    order_files = list_new_files("validated/orders/")
    item_files = list_new_files("validated/order_items/")
    if not order_files or not item_files:
        print("No new validated files to process.")
        return

    orders_key = sorted(order_files)[-1]
    items_key = sorted(item_files)[-1]
    products_path = get_latest_product_file(PRODUCTS_PREFIX)

    orders_path = f"s3a://{BUCKET}/{orders_key}"
    items_path = f"s3a://{BUCKET}/{items_key}"

    orders = spark.read.option("header", True).csv(orders_path)
    items = spark.read.option("header", True).csv(items_path)
    products = spark.read.option("header", True).csv(products_path)

    orders = (
        orders.withColumn("order_date", to_date(col("created_at")))
        .withColumn("num_of_item", col("num_of_item").cast(IntegerType()))
    )

    items = (
        items.withColumn("order_date", to_date(col("created_at")))
        .withColumn("is_returned", expr("status = 'returned'"))
        .withColumn("sale_price", col("sale_price").cast(DecimalType(10, 2)))
    )

    # --- CATEGORY KPI ---
    merged = items.join(products, items.product_id == products.id)

    category_df = merged.groupBy("order_id", "category", "order_date").agg(
        _sum("sale_price").alias("order_value"),
        _max(when(col("is_returned"), 1).otherwise(0)).alias("returned_flag")
    )

    category_kpi = category_df.groupBy("category", "order_date").agg(
        _sum("order_value").alias("daily_revenue"),
        avg("order_value").alias("avg_order_value"),
        avg("returned_flag").alias("avg_return_rate")
    )

    category_records = [
        {
            "category": row["category"],
            "order_date": str(row["order_date"]),
            "daily_revenue": row["daily_revenue"],
            "avg_order_value": row["avg_order_value"],
            "avg_return_rate": row["avg_return_rate"],
        }
        for row in category_kpi.collect()
    ]
    write_to_dynamodb(category_table, category_records)

    # --- ORDER KPI ---
    order_revenue = items.groupBy("order_id").agg(
        _sum("sale_price").alias("order_revenue")
    )
    merged_orders = orders.join(order_revenue, on="order_id", how="left")

    order_kpi = merged_orders.groupBy("order_date").agg(
        countDistinct("order_id").alias("total_orders"),
        _sum("order_revenue").alias("total_revenue"),
        _sum("num_of_item").alias("total_items_sold"),
        avg(expr("CASE WHEN status = 'returned' THEN 1 ELSE 0 END")).alias("return_rate"),
        countDistinct("user_id").alias("unique_customers"),
    )

    order_records = [
        {
            "order_date": str(row["order_date"]),
            "total_orders": int(row["total_orders"]),
            "total_revenue": row["total_revenue"],
            "total_items_sold": int(row["total_items_sold"]),
            "return_rate": row["return_rate"],
            "unique_customers": int(row["unique_customers"]),
        }
        for row in order_kpi.collect()
    ]
    write_to_dynamodb(order_table, order_records)

    for key in [orders_key, items_key]:
        mark_as_processed(key)
        archive_file(key)

    print("Transformation complete and archived successfully.")

if __name__ == "__main__":
    handler()