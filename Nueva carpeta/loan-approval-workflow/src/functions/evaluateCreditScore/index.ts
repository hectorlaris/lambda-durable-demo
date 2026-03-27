import { APIGatewayEvent, Context } from 'aws-lambda';
import axios from 'axios';
import { LoanApplication } from '../../types';

export const evaluateCreditScore = async (event: APIGatewayEvent, context: Context): Promise<any> => {
    const applicationId = event.pathParameters?.id;

    if (!applicationId) {
        return {
            statusCode: 400,
            body: JSON.stringify({ message: 'Application ID is required' }),
        };
    }

    try {
        // Fetch loan application data from the API
        const response = await axios.get<LoanApplication>(`https://api.example.com/loan-applications/${applicationId}`);
        const applicationData = response.data;

        // Evaluate credit score based on predefined criteria
        const creditScore = applicationData.creditScore;
        let evaluationResult;

        if (creditScore >= 700) {
            evaluationResult = 'Approved';
        } else if (creditScore >= 600) {
            evaluationResult = 'Review';
        } else {
            evaluationResult = 'Rejected';
        }

        return {
            statusCode: 200,
            body: JSON.stringify({ applicationId, evaluationResult }),
        };
    } catch (error) {
        console.error('Error evaluating credit score:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ message: 'Internal server error' }),
        };
    }
};