import { dynamoClient } from './dynamoClient';
import { LoanApplication } from '../types';

const LOAN_TABLE = process.env.LOAN_TABLE || '';

export const saveLoanApplication = async (application: LoanApplication) => {
    const params = {
        TableName: LOAN_TABLE,
        Item: application,
    };
    await dynamoClient.put(params).promise();
};

export const getLoanApplication = async (applicationId: string) => {
    const params = {
        TableName: LOAN_TABLE,
        Key: {
            id: applicationId,
        },
    };
    const result = await dynamoClient.get(params).promise();
    return result.Item as LoanApplication | undefined;
};

export const updateLoanApplication = async (applicationId: string, updates: Partial<LoanApplication>) => {
    const params = {
        TableName: LOAN_TABLE,
        Key: {
            id: applicationId,
        },
        UpdateExpression: 'set #status = :status, #updatedAt = :updatedAt',
        ExpressionAttributeNames: {
            '#status': 'status',
            '#updatedAt': 'updatedAt',
        },
        ExpressionAttributeValues: {
            ':status': updates.status,
            ':updatedAt': new Date().toISOString(),
        },
    };
    await dynamoClient.update(params).promise();
};