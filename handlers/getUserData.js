const AWS = require('aws-sdk');

const dynamoDB = new AWS.DynamoDB.DocumentClient();
const tableName = 'bites-user-data-dev';

module.exports.handler = async (event) => {
    const id = event.queryStringParameters.id;
    const sortKey = event.queryStringParameters.sortKey;

    const params = {
        TableName: tableName,
        Key: {
        PK: `USER#${id}`,
        SK: sortKey,
        },
    };

    try {
        const data = await dynamoDB.get(params).promise();
        return {
        statusCode: 200,
        headers: {
            "Content-Type": "application/json",
            'Access-Control-Allow-Origin' : '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'OPTIONS, GET'
        },
        body: JSON.stringify(data.Item),
        };
    } catch (error) {
        console.error('Error retrieving item:', error);
        return {
        statusCode: 500,
        body: JSON.stringify({ error: 'An error occurred while retrieving the item' }),
        };
    }
};