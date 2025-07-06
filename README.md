# ECS Event-Driven Data Pipeline

## Overview

This project implements a **real-time**, **event-driven data pipeline** for an e-commerce platform using AWS services. It ingests transactional data (CSV files) uploaded to Amazon S3, validates and transforms it using containerized tasks on ECS (Fargate), stores business KPIs in DynamoDB, and uses AWS Step Functions to orchestrate the process. The workflow is triggered by S3 events through a Lambda function.

### Key Features

* **Event-Driven Trigger**: S3 upload triggers Lambda to start Step Functions
* **Containerized Processing**: ECS Fargate runs validator & transformer containers
* **Automated Orchestration**: Step Functions handles task coordination, error recovery, and cleanup
* **Optimized Storage**: KPIs stored in DynamoDB for fast, structured querying
* **Resource Cleanup**: All ephemeral resources are automatically deleted after use
* **Robust Error Handling**: Retry policies, SNS notifications, and logging via CloudWatch
* **File Archiving**: Validated files are moved to a `processed/` prefix in S3

---

## Repository Structure

```bash
ephemeral-ecs-pipeline/
├── .github/workflows/
│   └── main.yml                 # GitHub Actions for CI/CD
├── step_functions/
│   └── MainStepFn.json          # Step Functions definition
├── iam/
│   └── ecsExecutionTaskRole.json  # IAM policies for ECS roles
│   └── ecsTaskRole.json
├── ecs/
│   ├── validator/
│   │   ├── Dockerfile
│   │   └── validator.py
│   ├── transformer/
│   │   ├── Dockerfile
│   │   └── transformer.py
├── data
│   ├── products/
│   ├── orders/
│   └── order_items/
├── tests/
│   ├── test_lambda.py
│   └── test_pipeline.sh
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   ├── testing.md
│   └── troubleshooting.md
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

---

## Prerequisites

* AWS CLI configured (`aws configure`)
* Docker
* AWS IAM roles and policies
* ECR repos for containers
* S3 bucket for input files
* DynamoDB tables for KPIs

IAM Roles:

* `ecsTaskExecutionRole`
* `ecsTaskRole`
* `stepFunctionsExecutionRole`
* `lambdaExecutionRole`

SNS Topics:

* `ecommerce-pipeline-success`
* `ecommerce-pipeline-failure`

---

## Data Flow and Design

### Input Format (CSV)

```csv
order_id,customer_id,order_date,category,product_id,quantity,unit_price,returned
ORD123,CUST001,2025-07-06,Electronics,PROD001,2,199.99,false
```

### Validator (ecs/validator/validator.py)

* Ensures required fields, correct data types, valid formats, and integrity
* Fails the pipeline on invalid data

### Transformer (ecs/transformer/transformer.py)

* Calculates:

  * **Order KPIs**: total revenue, return rate, etc.
  * **Category KPIs**: average order value, daily revenue
* Writes to `OrderKPIs` and `CategoryKPIs` DynamoDB tables

### DynamoDB Tables

#### CategoryKPIs

* `Partition Key`: category
* `Sort Key`: order\_date
* Attributes: daily\_revenue, avg\_order\_value, avg\_return\_rate

#### OrderKPIs

* `Partition Key`: order\_date
* Attributes: total\_orders, total\_revenue, total\_items\_sold, return\_rate, unique\_customers

---

## Deployment

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/ephemeral-ecs-pipeline.git
cd ephemeral-ecs-pipeline
```

### 2. Create AWS Resources

```bash
# S3 Bucket
aws s3 mb s3://<your-bucket> --region <your-region>

# DynamoDB Tables
aws dynamodb create-table ... # See docs

# ECR Repos
aws ecr create-repository --repository-name ecs-validator
aws ecr create-repository --repository-name ecs-transformer
```

### 3. Build & Push Containers

```bash
cd ecs/validator
# Build and push to ECR

cd ../transformer
# Build and push to ECR
```

### 4. Setup Eventsbridge 

```bash
add a rule
```

### 5. Configure S3 Event Notifications

```bash
aws s3api put-bucket-notification-configuration ...
```

### 6. Deploy Step Functions

```bash
aws stepfunctions create-state-machine ...
```

### 7. Run Test Pipeline

```bash
aws s3 cp data/sample/valid_order.csv s3://<your-bucket>/input/test.csv
```

---

## 🔮 CI/CD with GitHub Actions

* Defined in `.github/workflows/main.yml`
* Auto-deploys Lambda, Step Function updates, and validates JSON syntax
* Secrets should be stored securely via GitHub Settings

---

## 📊 Monitoring and Logs

* **CloudWatch Logs**:

  * `/ecs/ephemeral-pipeline`
  * Stream prefixes: `ecs-validator`, `ecs-transformer`
* **SNS Alerts** for both success and failure
* **Step Function Execution History**: view full pipeline execution state

---

## 🔬 Testing & Simulation

```bash
# Manual trigger
aws stepfunctions start-execution --input '{"bucket": "<your-bucket>", "key": "input/test.csv"}'

# Run unit tests
pytest tests/test_lambda.py

# Simulate end-to-end
./tests/test_pipeline.sh
```

---

## Future Improvements

* Add SQS DLQ for failed files
* Build a frontend dashboard to query KPIs
* Extend validation rules and schema flexibility
* Create a visual architecture diagram using draw\.io

---

## 📖 License

MIT License. See `LICENSE` file.

##  Contributing

* Fork and clone
* Create feature branches
* Submit pull requests with clear descriptions

---

## Contact

For questions or support, open an issue on the GitHub repository.

---

Happy building with AWS! 🚀
