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