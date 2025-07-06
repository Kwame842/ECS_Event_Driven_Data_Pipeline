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