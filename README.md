# 🛡️ Phishing URL Detection System (AI + AWS)

An AI-powered cybersecurity project that detects phishing URLs using AWS services like SageMaker, Lambda, API Gateway, and DynamoDB.

---

## 🧠 Architecture Overview
![Architecture](docs/architecture-diagram.png)

---

## ⚙️ Tech Stack
- **AWS SageMaker** – Model training & deployment
- **AWS Lambda** – Serverless inference
- **Amazon API Gateway** – REST API endpoint
- **Amazon DynamoDB** – Store prediction logs
- **Amazon S3** – Dataset & model storage

---

## 🚀 Setup Guide

### 1️⃣ Dataset Preparation
Upload `phishing_dataset1.csv` to an S3 bucket.

### 2️⃣ Train Model
Run `model/training/train_model.ipynb` in SageMaker to:
- Extract URL features
- Train classifier (XGBoost or Logistic Regression)
- Save model artifact to S3

### 3️⃣ Deploy Model
Deploy using `model/deployment/deploy_model.ipynb`.
This creates a SageMaker endpoint for real-time inference.

### 4️⃣ Setup Lambda + API Gateway
- Deploy `lambda/lambda_function.py`
- Connect to SageMaker endpoint
- Create REST API in API Gateway

### 5️⃣ DynamoDB
Create a table named `PhishingDetections` with:
```json
{
  "url": "String (Primary Key)",
  "prediction": "String",
  "score": "Number",
  "timestamp": "String"
}
