import boto3
import json
import re
from datetime import datetime

sagemaker_client = boto3.client('runtime.sagemaker')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('PhishingDetections')

def extract_features(url):
    return [
        len(url),
        url.count('.'),
        url.count('-'),
        url.count('@'),
        int('https' in url),
        int('login' in url)
    ]

def lambda_handler(event, context):
    url = event.get('url')
    features = extract_features(url)
    
    response = sagemaker_client.invoke_endpoint(
        EndpointName='phishing-detector-endpoint',
        ContentType='text/csv',
        Body=','.join(map(str, features))
    )
    
    result = json.loads(response['Body'].read().decode())
    prediction = "phishing" if result > 0.5 else "legit"
    
    table.put_item(Item={
        'url': url,
        'prediction': prediction,
        'score': float(result),
        'timestamp': datetime.utcnow().isoformat()
    })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'url': url,
            'prediction': prediction,
            'confidence': round(float(result), 2)
        })
    }
