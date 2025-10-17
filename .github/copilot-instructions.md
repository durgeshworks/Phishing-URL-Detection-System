# AI Agent Instructions for Phishing URL Detection System

## Project Overview
This is an AWS-based ML system that detects phishing URLs through a serverless architecture. The system uses SageMaker for model training/deployment, Lambda for inference, and DynamoDB for logging predictions.

## Key Components & Data Flow
1. **Data Processing Pipeline** (`data/notebooks/`)
   - Raw phishing datasets in `data/raw/` → Feature extraction → Processed features
   - Key features: URL length, special character counts, HTTPS presence, suspicious terms

2. **Model Training** (`model/training/train_model.ipynb`)
   - Reads processed data from S3
   - Trains XGBoost/Logistic Regression classifier
   - Saves model artifacts to S3

3. **Inference Pipeline** (`lambda/lambda_function.py`)
   - REST API → API Gateway → Lambda
   - Lambda extracts features and calls SageMaker endpoint
   - Predictions stored in DynamoDB

## Development Workflows

### Setting Up Local Environment
1. AWS credentials must be configured for:
   - S3 bucket access (datasets/models)
   - SageMaker notebook instances
   - Lambda deployment
   - DynamoDB table management

### Model Development
- Feature engineering logic is shared between training (`data_preparation.ipynb`) and inference (`lambda_function.py`)

### Deployment Pipeline
1. Train model using SageMaker notebook
2. Deploy model endpoint via `model/deployment/deploy_model.ipynb`
3. Update Lambda with new endpoint name if changed

## Project Conventions

### Data Storage
- Raw datasets: `data/raw/`
- Processed features: `data/processed/`
- Model artifacts: S3 bucket (defined in training notebook)

### DynamoDB Schema
```json
{
  "url": "String (Primary Key)",
  "prediction": "String (phishing/legit)",
  "score": "Number (0-1)",
  "timestamp": "String (ISO format)"
}
```

### Key Integration Points
- SageMaker endpoint name must match in deployment notebook and Lambda function
- Lambda expects URL features in specific CSV format for inference
- DynamoDB table name "PhishingDetections" is hardcoded in Lambda

## Common Development Tasks
- Testing model changes: Update feature extraction locally before deploying
- Debugging predictions: Check DynamoDB logs for specific URLs
- Updating dependencies: Manage both notebook and Lambda requirements separately