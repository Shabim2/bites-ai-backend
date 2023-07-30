const AWS = require('aws-sdk');
const { Configuration, OpenAIApi } = require("openai");

module.exports.handler = async (event) => {
    const ssm = new AWS.SSM();

    const params = {
        Name: 'openai_DEV',
        WithDecryption: true // Specify this if the parameter value is encrypted
      };

    try {
        const{
            food
        } = JSON.parse(event.body)

        const response = await ssm.getParameter(params).promise();
        const parameterValue = response.Parameter.Value;


        const configuration = new Configuration({
            apiKey: parameterValue,
          });
        const openai = new OpenAIApi(configuration);
    
        // Query OpenAI's GPT model for an estimate of the calorie content
        const chatCompletion = await openai.createChatCompletion({
        model: "gpt-3.5-turbo",
        messages: [
          {role: "system", content: "You are a concise assistant that knows the calorie amount, the amount of protein in grams, the amount of carbs in grams, and the amount of fat in grams of a given food."},
          {role: "user", content: `How many calories, protein, carbs, and fat does ${food} have? respond with only a json object string formatted like this {"calories":"", "protein":"", carbs:"", fats:""}`}
        ],
        temperature: 1,
        max_tokens: 32,
        n: 1
        });

      return {
            statusCode: 200,
            headers: {
                "Content-Type": "application/json",
                'Access-Control-Allow-Origin' : '*',
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