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