const AWS = require('aws-sdk');
const { Configuration, OpenAIApi } = require("openai");

module.exports.handler = async (event) => {

    const params = {
        Name: 'openai_DEV',
        WithDecryption: true // Specify this if the parameter value is encrypted
      };

    try {
        const{
            weight,
            height,
            age,
            gender,
            userid
        } = JSON.parse(event.body)


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