import { APIGatewayEvent, Context } from 'aws-lambda';
import axios from 'axios';
import { LoanApplication } from '../../types';

export const submitLoanApplication = async (event: APIGatewayEvent, context: Context) => {
    const application: LoanApplication = JSON.parse(event.body || '{}');

    try {
        const response = await axios.post('https://api.example.com/loan/apply', application);
        return {
            statusCode: 200,
            body: JSON.stringify({
                message: 'Loan application submitted successfully',
                data: response.data,
            }),
        };
    } catch (error) {
        return {
            statusCode: error.response?.status || 500,
            body: JSON.stringify({
                message: 'Failed to submit loan application',
                error: error.message,
            }),
        };
    }
};