const AWS = require('aws-sdk');
const { Configuration, OpenAIApi } = require("openai");
const util = require('util')
const stream = require('stream')

const ssm = new AWS.SSM();

const params = {
    Name: 'openai_DEV',
    WithDecryption: true // Specify this if the parameter value is encrypted
};

const response = ssm.getParameter(params).promise();
const parameterValue = response.Parameter.Value;


const configuration = new Configuration({
    apiKey: parameterValue,
});
const openai = new OpenAIApi(configuration);

const pipeline = util.promisify(stream.pipeline);

/* global awslambda */
module.exports.handler = awslambda.streamifyResponse(
    async (event, responseStream, _context) => {
        const stream = await openai.chat.completions.create({
            model: 'gpt-3.5-turbo',
            messages: [{ role: 'user', content: 'Say this is a test' }],
            stream: true,
        });
        for await (const part of stream) {
            const requestStream = Readable.from(Buffer.from(JSON.stringify(part.choices[0]?.delta?.content)));
            process.stdout.write(part.choices[0]?.delta?.content || '');
            pipeline(requestStream,responseStream)
        }
    }
);