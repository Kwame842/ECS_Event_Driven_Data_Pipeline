import json
import boto3
import os
import logging
from datetime import datetime
from botocore.exceptions import ClientError, BotoCoreError

# Setup structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
EVENT_BUS_NAME = os.environ.get("EVENT_BUS_NAME", "default")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "<Your bucket Name>")
FOLDER_PREFIX = "incoming/"
STEP_FUNCTION_DETAIL_TYPE = "StartEphemeralPipeline"

events_client = boto3.client("events")

def lambda_handler(event, context):
    try:
        if "Records" not in event:
            logger.warning("No records found in event.")
            return _response(400, "No S3 records in event.")

        for record in event["Records"]:
            s3_bucket = record["s3"]["bucket"]["name"]
            s3_key = record["s3"]["object"]["key"]
            logger.info(f"Received file: s3://{s3_bucket}/{s3_key}")

            if s3_bucket != S3_BUCKET_NAME or not s3_key.startswith(FOLDER_PREFIX):
                logger.info(f"Skipping non-matching file: {s3_key}")
                continue

            detail = {
                "bucket": s3_bucket,
                "key": s3_key,
                "timestamp": datetime.utcnow().isoformat()
            }

            response = events_client.put_events(
                Entries=[
                    {
                        "Source": "custom.s3.upload",
                        "DetailType": STEP_FUNCTION_DETAIL_TYPE,
                        "Detail": json.dumps(detail),
                        "EventBusName": EVENT_BUS_NAME
                    }
                ]
            )

            failed_count = response.get("FailedEntryCount", 0)
            if failed_count > 0:
                logger.error(f"Failed to emit event: {response}")
                return _response(500, f"Failed to emit event for {s3_key}")
            else:
                logger.info(f"Successfully emitted event for {s3_key}")

        return _response(200, "Event(s) processed successfully.")

    except (ClientError, BotoCoreError) as boto_err:
        logger.exception("Boto3 error while emitting EventBridge event")
        return _response(500, str(boto_err))

    except Exception as e:
        logger.exception("Unhandled exception")
        return _response(500, f"Unexpected error: {str(e)}")


def _response(code, message):
    return {
        "statusCode": code,
        "body": json.dumps({"message": message})
    }
