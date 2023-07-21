require('dotenv').config();
const { Configuration, OpenAIApi } = require("openai");
const readline = require('readline');

const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
});
const openai = new OpenAIApi(configuration);

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

rl.question('Please enter the food you want to know the calories of: ', async (food) => {

    // Query OpenAI's GPT model for an estimate of the calorie content
    const chatCompletion = await openai.createChatCompletion({
      model: "gpt-3.5-turbo",
      messages: [
        {role: "system", content: "You are a concise assistant that knows about calorie amounts in food, don't include explanations or exposition text in your response"},
        {role: "user", content: `How many calories are in ${food}?`}
      ],
    });

    console.log(`Estimated calories: ${chatCompletion.data.choices[0].message.content}`);
    rl.close();
});


