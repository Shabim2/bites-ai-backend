const AWS = require('aws-sdk');

const s3 = new AWS.S3();
const dynamoDB = new AWS.DynamoDB.DocumentClient();
const tableName = 'bites-user-data-dev';

exports.handler = async (event) => {
    const { filename, id } = JSON.parse(event.body);

    const s3KeyPrefix = `${id}/`;

    const params = {
        Bucket: 'bites-ai-dev',
        Key: s3KeyPrefix + filename,
        Expires: 3600, // URL expires in 1 hour (adjust as needed)
        ContentType: 'application/xml', // Set the content type of the uploaded file
      };

    entry = ''
    filename ? entry = `${id}/${filename}` : entry = ''
    const entryData = {
        // Provide the data you want to upload here, e.g., 'userId', 'timestamp', 'otherAttributes', etc.
        PK: `USER#${id}`,
        SK: 'Watch',
        entry
    };

    const dbParams = {
        TableName: tableName,
        Item: entryData,
    };

    try {
        const uploadURL = await s3.getSignedUrlPromise('putObject', params);
        await dynamoDB.put(dbParams).promise();
        return {
        statusCode: 200,
        body: JSON.stringify({ uploadURL }),
        headers: {
            "Content-Type": "application/json",
            'Access-Control-Allow-Origin' : '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'OPTIONS, POST'
        },
        };
    } catch (error) {
        return {
        statusCode: 500,
        body: JSON.stringify({ message: 'Error uploading file to S3.', error }),
        };
    }
    };