import pandas as pd
import boto3
import io
from datetime import datetime, timedelta
import json


def handler(event, context):
    # Get the S3 bucket and object key from the API request
    s3 = boto3.client('s3')
    bucket_name = event['queryStringParameters']['bucketName']
    object_key = event['queryStringParameters']['objectKey']

    # Read the CSV file from S3
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    csv_content = response['Body'].read().decode('utf-8')

    # Load CSV content into a pandas DataFrame
    df = pd.read_csv(io.StringIO(csv_content))

    # Convert 'endtime' column to datetime with timezone (assuming it's in UTC)
    df['endtime'] = pd.to_datetime(df['endtime']).dt.tz_convert('UTC')

    # Find the latest date in the data
    latest_date = df['endtime'].max()

    # Calculate the date 30 days ago from the latest date in UTC timezone
    last_30_days = latest_date - timedelta(days=30)

    # Filter data for the latest 30 days
    df = df[df['endtime'] >= last_30_days]

    # Extract the date from 'endtime' and group by date to calculate the total calories spent per day
    df['date'] = df['endtime'].dt.date
    result = df.groupby('date')['value'].sum().reset_index()

    # Convert the 'date' values to strings to make them JSON serializable
    result['date'] = result['date'].astype(str)

    # Convert the DataFrame to an array of dictionaries (list of objects)
    data_array = result.to_dict(orient='records')


    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            'Access-Control-Allow-Origin' : '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'OPTIONS, GET'
        },
        "body": json.dumps(data_array)
    }