# ECS_Event_Driven_Data_Pipeline

Real-Time Event-Driven Data Pipeline for E-Commerce
Overview
This project implements a real-time, event-driven data pipeline to support operational analytics for an e-commerce platform, as specified in Project 5_ECS.pdf. The pipeline processes transactional data arriving as CSV files in an Amazon S3 bucket, validates and transforms the data using containerized services on Amazon ECS (Fargate), computes business KPIs, stores results in Amazon DynamoDB for real-time querying, and automates the workflow using AWS Step Functions. An AWS Lambda function triggers the pipeline on S3 events. The solution is scalable, fault-tolerant, and fully automated, with comprehensive logging, error handling, notifications, and resource cleanup.
Key Features

Event-Driven Trigger: S3 events trigger a Lambda function to start the Step Functions workflow.
Containerized Processing: ECS Fargate runs validator and transformer tasks in parallel.
Automated Orchestration: Step Functions manages cluster creation, task execution, cleanup, and file archiving.
Optimized Storage: Stores Category-Level and Order-Level KPIs in DynamoDB with efficient access patterns.
Resource Cleanup: Deregisters task definitions and deletes ECS clusters to prevent orphaned resources.
Error Handling: Includes retries, SNS notifications for success/failure, and CloudWatch logging.
File Archiving: Moves processed files to a processed/ prefix in S3.

Repository Structure
The GitHub repository is organized as follows:
ephemeral-ecs-pipeline/
├── .github/
│   └── workflows/
│       └── main.yml                         # GitHub Actions CI/CD pipeline for deployment
├── step_functions/
│   └── MainStepFn.json                      # Step Functions state machine JSON
├── iam/
│   └── ecsExecutionTaskRole.json            # IAM policy for ECS task role
├── ecs/
│   ├── validator/
│   │   ├── Dockerfile                       # Dockerfile for validator container
│   │   └── validator.py                     # Python logic for data validation
│   ├── transformer/
│   │   ├── Dockerfile                       # Dockerfile for transformer container
│   │   └── transformer.py                   # Python logic for KPI computation and 
├── data/
│   ├── sample/
│   │   ├── valid_order.csv                  # Sample valid CSV for testing
│   │   └── invalid_order.csv                # Sample invalid CSV for failure testing
├── .gitignore                               # Git ignore file for credentials, temp files
├── LICENSE                                  # MIT License file
├── README.md                                # This file (project overview, setup, usage)
└── requirements.txt                         # Development dependencies (e.g., boto3, pytest)

Directory and File Descriptions

.github/workflows/main.yml: GitHub Actions workflow for CI/CD to deploy Lambda, Step Functions, and other resources.
step_functions/MainStepFn.json: AWS Step Functions state machine definition for orchestrating the pipeline.
iam/ecs-task-role-policy.json: IAM policy for the ECS task role, granting permissions for S3 reads and DynamoDB writes.
ecs/validator/Dockerfile: Dockerfile for building the validator container image.
ecs/validator/validator.py: Python script for validating CSV data (checks format, required fields, data types).
ecs/transformer/Dockerfile: Dockerfile for building the transformer container image.
ecs/transformer/transformer.py: Python script for computing KPIs and writing to DynamoDB.
lambda/s3_trigger/lambda_function.py: Lambda function to trigger Step Functions on S3 events.
lambda/s3_trigger/requirements.txt: Python dependencies for the Lambda function (e.g., boto3).
scripts/deploy.sh: Shell script to deploy S3, DynamoDB, Lambda, and Step Functions resources.
scripts/undeploy.sh: Shell script to clean up deployed resources.
scripts/validate_json.sh: Script to validate MainStepFn.json syntax using jq.
data/sample/valid_order.csv: Sample valid CSV for testing the pipeline.
data/sample/invalid_order.csv: Sample invalid CSV to test validation failures.
tests/test_lambda.py: Unit tests for the Lambda function using pytest and moto.
tests/test_pipeline.sh: Script to simulate pipeline execution by uploading test files.
docs/architecture.md: Architecture overview with a pipeline diagram.
docs/setup.md: Detailed setup and deployment instructions.
docs/testing.md: Guidelines for manual and automated testing.
docs/troubleshooting.md: Common issues and solutions.
.gitignore: Ignores sensitive files (e.g., .env, AWS credentials, *.pyc).
LICENSE: MIT License for open-source usage.
README.md: This file, providing project overview, setup, and usage.
requirements.txt: Development dependencies (e.g., boto3, pytest).

Prerequisites
To deploy and use this pipeline, you need:

An AWS account with permissions for:
Amazon S3 (bucket creation, event notifications)
Amazon ECS (cluster and task management)
AWS Step Functions (state machine execution)
Amazon DynamoDB (table creation and writes)
AWS Lambda (event triggering)
Amazon SNS (notifications)
Amazon CloudWatch (logging)
AWS IAM (role and policy management)
Amazon ECR (container image storage)


AWS CLI configured with credentials (aws configure).
AWS SDK or AWS Management Console for deployment.
Docker for building and pushing ECS container images.
Container Images in Amazon ECR:
Validator: <AWS_ACCOUNT_ID>.dkr.ecr.<YOUR_REGION>.amazonaws.com/ecs-validator:latest
Transformer: <AWS_ACCOUNT_ID>.dkr.ecr.<YOUR_REGION>.amazonaws.com/ecs-transformer:latest


IAM Roles (replace ARNs with your own):
ecsTaskExecutionRole: For ECS task execution.
ecsTaskRole: For task permissions (S3 read, DynamoDB write).
stepFunctionsExecutionRole: For Step Functions to call ECS and SNS.
lambdaExecutionRole: For Lambda to trigger Step Functions.


SNS Topics (create and use your own ARNs):
Success topic: arn:aws:sns:<YOUR_REGION>:<AWS_ACCOUNT_ID>:ecommerce-pipeline-success
Failure topic: arn:aws:sns:<YOUR_REGION>:<AWS_ACCOUNT_ID>:ecommerce-pipeline-failure


CloudWatch Log Group: /ecs/ephemeral-pipeline
VPC Configuration:
Subnets: At least two subnets in your VPC.
Security Groups: Configured for ECS task communication.


S3 Bucket: <YOUR_BUCKET_NAME> for input files (input/) and processed file archiving (processed/).
DynamoDB Tables:
OrderKPIs: For Order-Level KPIs.
CategoryKPIs: For Category-Level KPIs.



Note: Replace placeholders (e.g., <AWS_ACCOUNT_ID>, <YOUR_REGION>, <YOUR_BUCKET_NAME>) with your actual AWS resource values before deployment.
Data Format and Sample Schema
Input Data
Transactional data arrives as CSV files in <YOUR_BUCKET_NAME>/input/. Example:
order_id,customer_id,order_date,category,product_id,quantity,unit_price,returned
ORD123,CUST001,2025-07-06,Electronics,PROD001,2,199.99,false
ORD124,CUST002,2025-07-06,Books,PROD002,1,29.99,true


Fields:
order_id: Unique order identifier (string).
customer_id: Unique customer identifier (string).
order_date: Date of the order (YYYY-MM-DD).
category: Product category (e.g., Electronics, Books).
product_id: Unique product identifier (string).
quantity: Number of items ordered (integer).
unit_price: Price per item (float).
returned: Whether the order was returned (boolean).



Validation Rules
The validator task (ecs/validator/validator.py) checks:

Required Fields: All fields must be present.
Data Types:
order_id, customer_id, product_id, category: Non-empty strings.
order_date: Valid YYYY-MM-DD format.
quantity: Positive integer.
unit_price: Positive float.
returned: Boolean (true or false).


Referential Integrity:
order_id: Unique within the file.
category: Must be in a predefined list (e.g., Electronics, Books, Clothing).


File Format: Valid CSV with a header row.
Action on Failure: Rejects the file, triggers an SNS failure notification, and exits the pipeline.

Output Data
The transformer task (ecs/transformer/transformer.py) computes KPIs:

Category-Level KPIs (CategoryKPIs table):{
  "category": "Electronics",
  "order_date": "2025-07-06",
  "daily_revenue": 399.98,
  "avg_order_value": 199.99,
  "avg_return_rate": 0.0
}


Order-Level KPIs (OrderKPIs table):{
  "order_date": "2025-07-06",
  "total_orders": 2,
  "total_revenue": 429.97,
  "total_items_sold": 3,
  "return_rate": 0.5,
  "unique_customers": 2
}



DynamoDB Table Structure and Access Patterns
Table: CategoryKPIs

Partition Key: category (string)
Sort Key: order_date (string, YYYY-MM-DD)
Attributes:
daily_revenue: Number (total revenue for the category).
avg_order_value: Number (average order value).
avg_return_rate: Number (percentage of returned orders).


Access Patterns:
Query by category and date range (e.g., Electronics KPIs for July 2025).
Query by category for a specific date.


Secondary Indexes: None, as primary key supports main access patterns.

Table: OrderKPIs

Partition Key: order_date (string, YYYY-MM-DD)
Attributes:
total_orders: Number (count of unique orders).
total_revenue: Number (total revenue).
total_items_sold: Number (total items sold).
return_rate: Number (percentage of returned orders).
unique_customers: Number (distinct customers).


Access Patterns:
Query KPIs for a specific date.
Query KPIs for a date range.


Secondary Indexes: None, as partition key supports primary access pattern.

Design Justification

Separate Tables: Optimizes for distinct access patterns, avoiding complex indexing.
Key Selection: category and order_date enable efficient queries for analytics.
Scalability: Initial throughput (5 RCUs/WCUs) can be adjusted or switched to on-demand mode.

Setup Instructions

Clone the Repository:
git clone https://github.com/<YOUR_USERNAME>/ephemeral-ecs-pipeline.git
cd ephemeral-ecs-pipeline


Create AWS Resources:

S3 Bucket:aws s3 mb s3://<YOUR_BUCKET_NAME> --region <YOUR_REGION>


DynamoDB Tables:aws dynamodb create-table \
  --table-name CategoryKPIs \
  --attribute-definitions AttributeName=category,AttributeType=S AttributeName=order_date,AttributeType=S \
  --key-schema AttributeName=category,KeyType=HASH AttributeName=order_date,KeyType=RANGE \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region <YOUR_REGION>
aws dynamodb create-table \
  --table-name OrderKPIs \
  --attribute-definitions AttributeName=order_date,AttributeType=S \
  --key-schema AttributeName=order_date,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region <YOUR_REGION>


ECR Repositories:aws ecr create-repository --repository-name ecs-validator --region <YOUR_REGION>
aws ecr create-repository --repository-name ecs-transformer --region <YOUR_REGION>


Build and Push Containers:cd ecs/validator
docker build -t ecs-validator .
aws ecr get-login-password --region <YOUR_REGION> | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.<YOUR_REGION>.amazonaws.com
docker tag ecs-validator <AWS_ACCOUNT_ID>.dkr.ecr.<YOUR_REGION>.amazonaws.com/ecs-validator:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<YOUR_REGION>.amazonaws.com/ecs-validator:latest
cd ../transformer
docker build -t ecs-transformer .
docker tag ecs-transformer <AWS_ACCOUNT_ID>.dkr.ecr.<YOUR_REGION>.amazonaws.com/ecs-transformer:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<YOUR_REGION>.amazonaws.com/ecs-transformer:latest


SNS Topics:aws sns create-topic --name ecommerce-pipeline-success --region <YOUR_REGION>
aws sns create-topic --name ecommerce-pipeline-failure --region <YOUR_REGION>


CloudWatch Log Group:aws logs create-log-group --log-group-name /ecs/ephemeral-pipeline --region <YOUR_REGION>


IAM Roles: Create roles with policies:
ecsTaskExecutionRole: AmazonECSTaskExecutionRolePolicy.
ecsTaskRole: Permissions for S3 read, DynamoDB write (see iam/ecs-task-role-policy.json).
stepFunctionsExecutionRole: Permissions for ECS and SNS (ecs:*, sns:Publish).
lambdaExecutionRole: Permissions for Step Functions (states:StartExecution) and CloudWatch.




Deploy the Lambda Trigger:

Package and deploy the Lambda function:cd lambda/s3_trigger
zip -r s3_trigger.zip lambda_function.py requirements.txt
aws lambda create-function \
  --function-name S3Trigger \
  --runtime python3.9 \
  --role arn:aws:iam::<AWS_ACCOUNT_ID>:role/lambdaExecutionRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://s3_trigger.zip \
  --region <YOUR_REGION>


Configure S3 event notification:aws s3api put-bucket-notification-configuration \
  --bucket <YOUR_BUCKET_NAME> \
  --notification-configuration '{"LambdaFunctionConfigurations": [{"LambdaFunctionArn": "arn:aws:lambda:<YOUR_REGION>:<AWS_ACCOUNT_ID>:function:S3Trigger", "Events": ["s3:ObjectCreated:*"], "Filter": {"Key": {"FilterRules": [{"Name": "prefix", "Value": "input/"}]}}]}}'




Deploy the State Machine:

Replace placeholders in step_functions/MainStepFn.json.
Deploy:aws stepfunctions create-state-machine \
  --name EphemeralECSPipeline \
  --definition file://step_functions/MainStepFn.json \
  --role-arn arn:aws:iam::<AWS_ACCOUNT_ID>:role/stepFunctionsExecutionRole \
  --type STANDARD \
  --region <YOUR_REGION>




Run Deployment Script:
./scripts/deploy.sh



Step Function Workflow Explanation
The state machine (step_functions/MainStepFn.json) orchestrates the pipeline:

GenerateExecutionParameters (Pass):

Initializes configuration (execution ID, S3 bucket/key, ECR, IAM, VPC, SNS, DynamoDB).
Input: { "bucket": "<YOUR_BUCKET_NAME>", "key": "input/orders-2025-07-06.csv" }
Output: Stored in $.ephemeral.


CreateCluster (Task):

Creates an ECS cluster (ecs-ephemeral-cluster-<executionId>).
Uses aws-sdk:ecs:createCluster.
Output: $.clusterInfo.
Error: Transitions to NotifyPipelineFailure.


ProcessTasksInParallel (Parallel):

Runs two branches:
Validator Branch:
RegisterValidatorTask: Registers validator task definition.
RunValidator: Validates CSV data using ecs/validator/validator.py.


Transformer Branch:
RegisterTransformerTask: Registers transformer task definition.
RunTransformer: Computes KPIs and writes to DynamoDB using ecs/transformer/transformer.py.




Output: $.parallelResults.
Error: Transitions to Cleanup.


Cleanup (Parallel):

Deregisters task definitions:
DeregisterValidatorTask → SkipValidatorCleanup (on error).
DeregisterTransformerTask → SkipTransformerCleanup (on error).


Output: $.cleanupResults.
Error: Transitions to DeleteCluster.


DeleteCluster (Task):

Deletes the ECS cluster.
Output: $.deleteClusterResult.
Error: Transitions to ArchiveFile.


ArchiveFile (Task):

Copies the input file to processed/ using aws-sdk:s3:copyObject.
Output: $.archiveResult.
Error: Transitions to NotifyPipelineFailure.


DeleteSourceFile (Task):

Deletes the input file from input/ using aws-sdk:s3:deleteObject.
Output: $.deleteResult.
Error: Transitions to NotifyPipelineFailure.


NotifySuccess (Task):

Sends an SNS success notification.
Marks the end of execution.


NotifyPipelineFailure (Task):

Sends an SNS failure notification with error details.
Transitions to WorkflowFailed.


WorkflowFailed (Fail):

Terminates execution with a failure status.



State Machine JSON
See step_functions/MainStepFn.json (same as provided in the previous response, with placeholders for <AWS_ACCOUNT_ID>, <YOUR_REGION>, <YOUR_BUCKET_NAME>, etc.).
Error Handling, Retry, and Logging Logic
Error Handling

Catch Blocks:
CreateCluster, ProcessTasksInParallel, Cleanup, DeleteCluster, ArchiveFile, DeleteSourceFile: Catch all errors (States.ALL) and transition to NotifyPipelineFailure (or ArchiveFile for cleanup errors).
DeregisterValidatorTask, DeregisterTransformerTask: Transition to SkipValidatorCleanup or SkipTransformerCleanup on error.


Failure Notifications: NotifyPipelineFailure sends SNS notifications with execution ID, file details, and error information.

Retry Logic

RunValidator, RunTransformer:
Retry States.TaskFailed errors with:
Interval: 30 seconds
Max Attempts: 3
Backoff Rate: 2


Handles transient failures (e.g., container crashes, network issues).



Logging

CloudWatch Logs: Validator and transformer tasks log to /ecs/ephemeral-pipeline with prefixes ecs-validator and ecs-transformer.
Step Functions Execution History: Captures input/output for debugging.
SNS Notifications: Log success/failure with execution and file details.

Instructions to Simulate or Test the Pipeline Manually

Upload a Test File:

Use data/sample/valid_order.csv:order_id,customer_id,order_date,category,product_id,quantity,unit_price,returned
ORD123,CUST001,2025-07-06,Electronics,PROD001,2,199.99,false
ORD124,CUST002,2025-07-06,Books,PROD002,1,29.99,true


Upload:aws s3 cp data/sample/valid_order.csv s3://<YOUR_BUCKET_NAME>/input/test.csv




Manual Execution:
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:<YOUR_REGION>:<AWS_ACCOUNT_ID>:stateMachine:EphemeralECSPipeline \
  --input '{"bucket": "<YOUR_BUCKET_NAME>", "key": "input/test.csv"}' \
  --region <YOUR_REGION>


Monitor Execution:

Check Step Functions console for execution progress.
Verify CloudWatch logs (/ecs/ephemeral-pipeline).
Query DynamoDB:aws dynamodb query --table-name CategoryKPIs --key-condition-expression "category = :c and order_date = :d" --expression-attribute-values '{":c":{"S":"Electronics"},":d":{"S":"2025-07-06"}}' --region <YOUR_REGION>
aws dynamodb query --table-name OrderKPIs --key-condition-expression "order_date = :d" --expression-attribute-values '{":d":{"S":"2025-07-06"}}' --region <YOUR_REGION>


Check S3 processed/ prefix and SNS notifications.


Simulate Failures:

Upload data/sample/invalid_order.csv (e.g., missing order_id).
Verify RunValidator fails, triggers NotifyPipelineFailure, and sends an SNS notification.
Confirm file is not archived.


Run Tests:
pytest tests/test_lambda.py
./tests/test_pipeline.sh



Design Choices and Justifications

Event-Driven: S3 → Lambda → Step Functions ensures real-time processing.
Ephemeral ECS: Per-execution clusters isolate resources, preventing conflicts.
Parallel Tasks: Validator and transformer run concurrently for efficiency.
Fargate: Simplifies infrastructure management for short-lived tasks.
SNS Notifications: Provides immediate feedback for production monitoring.
DynamoDB Schema: Separate tables optimize query performance.
Repository Structure: Modular design (step_functions/, ecs/, lambda/) enhances maintainability.

Future Improvements

Dead-Letter Queue: Add SQS for failed files to enable reprocessing.
Dashboard: Create a web interface using API Gateway/Lambda to query KPIs.
Granular Errors: Add specific error conditions (e.g., AccessDeniedException).
Dynamic Inputs: Support customizable S3 prefixes or table names.
Monitoring: Add CloudWatch alarms for pipeline failures.

Contributing

Fork the repository.
Make changes (e.g., update MainStepFn.json, add tests).
Test locally using scripts/deploy.sh and tests/test_pipeline.sh.
Submit a pull request with a description of changes.

License
This project is licensed under the MIT License. See the LICENSE file.