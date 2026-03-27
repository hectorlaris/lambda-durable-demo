import { DynamoDB } from 'aws-sdk';
import { LoanApplication } from '../../types';

const dynamoClient = new DynamoDB.DocumentClient();
const TABLE_NAME = process.env.LOAN_APPLICATIONS_TABLE || '';

export const saveLoanApplication = async (application: LoanApplication) => {
    const params = {
        TableName: TABLE_NAME,
        Item: application,
    };
    await dynamoClient.put(params).promise();
};

export const getLoanApplication = async (applicationId: string) => {
    const params = {
        TableName: TABLE_NAME,
        Key: { id: applicationId },
    };
    const result = await dynamoClient.get(params).promise();
    return result.Item as LoanApplication | undefined;
};

export const updateLoanApplication = async (applicationId: string, updates: Partial<LoanApplication>) => {
    const params = {
        TableName: TABLE_NAME,
        Key: { id: applicationId },
        UpdateExpression: 'set #status = :status',
        ExpressionAttributeNames: {
            '#status': 'status',
        },
        ExpressionAttributeValues: {
            ':status': updates.status,
        },
    };
    await dynamoClient.update(params).promise();
};