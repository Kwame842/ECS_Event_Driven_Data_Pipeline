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