const AWS = require('aws-sdk');

const dynamoDB = new AWS.DynamoDB.DocumentClient();
const tableName = 'bites-user-data-dev';

module.exports.handler = async (event) => {
    try {
        const{
            weight,
            height,
            age,
            gender,
            id
        } = JSON.parse(event.body)

        const entryData = {
            // Provide the data you want to upload here, e.g., 'userId', 'timestamp', 'otherAttributes', etc.
            PK: `USER#${id}`,
            SK: 'BMR',
            weight,
            height,
            age,
            gender
          };

        const params = {
            TableName: tableName,
            Item: entryData,
          };
    
        const response = await dynamoDB.put(params).promise();
        console.log(response)
        return {
                statusCode: 200,
                headers: {
                    "Content-Type": "application/json",
                    'Access-Control-Allow-Origin' : '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'OPTIONS, POST'
                },
                body: 'success'
        }

        
    
    } catch (error) {
        // Handle any errors that occur during the retrieval
        console.error('Error retrieving parameter:', error);
    }
}