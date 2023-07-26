import pandas as pd
import boto3
import csv
import io

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

    # Convert 'endtime' column to datetime
    df['endtime'] = pd.to_datetime(df['endtime'])

    # Extract the date from 'endtime' and group by date to calculate the total calories spent per day
    df['date'] = df['endtime'].dt.date
    result = df.groupby('date')['value'].sum().reset_index()

    # Create the output CSV content
    output_csv = result.to_csv(index=False)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=calories_spent_per_day.csv"
        },
        "body": output_csv
    }