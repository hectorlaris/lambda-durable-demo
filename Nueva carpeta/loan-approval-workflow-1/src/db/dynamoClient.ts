import { DynamoDB } from 'aws-sdk';

const dynamoClient = new DynamoDB.DocumentClient();

export default dynamoClient;