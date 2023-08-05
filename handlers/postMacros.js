const AWS = require('aws-sdk');
const { Configuration, OpenAIApi } = require("openai");

module.exports.handler = async (event) => {
    try {
        const ssm = new AWS.SSM();

        const ssmParams = {
            Name: 'openai_DEV',
            WithDecryption: true // Specify this if the parameter value is encrypted
        };
        const {
            weight,
            height,
            age,
            gender,
            goals,
            id
        } = JSON.parse(event.body)

        const response = await ssm.getParameter(ssmParams).promise();
        const parameterValue = response.Parameter.Value;


        const configuration = new Configuration({
            apiKey: parameterValue,
        });
        const openai = new OpenAIApi(configuration);

        // Query OpenAI's GPT model for an estimate of the calorie content
        const chatCompletion = await openai.createChatCompletion({
            model: "gpt-3.5-turbo",
            messages: [
                { role: "system", content: "You are an assistant that gives nutrition information for your users who responds with only json formatted as {'calories':'', 'protein':'', 'carbs':'', 'fat':''}" },
                { role: "user", content: `How many grams of protein, carbs, fat, and total calories does an individual who weighs ${weight} kg, is ${height} cm tall, is a ${gender}, and is ${age} years old should have, (prioritize a high protein diet)? The individual has the following health and fitness goals ${goals}, respond with only a json object string formatted like this {"calories":"", "protein":"", carbs:"", fat:""}, return only a json object no other text` }
            ],
            temperature: 0,
            max_tokens: 100,
            n: 1
        });
        console.log(chatCompletion.data.choices[0].message.content)
        const dynamoDB = new AWS.DynamoDB.DocumentClient();
        const tableName = 'bites-user-data-dev';

        const entryData = {
            // Provide the data you want to upload here, e.g., 'userId', 'timestamp', 'otherAttributes', etc.
            PK: `USER#${id}`,
            SK: `Macros`,
            macros: JSON.parse(chatCompletion.data.choices[0].message.content),
            goals
        };

        const params = {
            TableName: tableName,
            Item: entryData,
        };
    
        await dynamoDB.put(params).promise();

        return {
            statusCode: 200,
            headers: {
                "Content-Type": "application/json",
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'OPTIONS, POST'
            },
            body: chatCompletion.data.choices[0].message.content
        }

    } catch (error) {
        // Handle any errors that occur during the retrieval
        console.error('Error retrieving parameter:', error);
    }
}