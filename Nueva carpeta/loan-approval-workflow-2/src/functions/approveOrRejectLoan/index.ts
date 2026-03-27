import { APIGatewayEvent, Context } from 'aws-lambda';
import axios from 'axios';

const LOAN_API_URL = process.env.LOAN_API_URL;

export const approveOrRejectLoan = async (event: APIGatewayEvent, context: Context) => {
    const { loanId, decision } = JSON.parse(event.body || '{}');

    if (!loanId || !decision) {
        return {
            statusCode: 400,
            body: JSON.stringify({ message: 'Loan ID and decision are required.' }),
        };
    }

    try {
        const response = await axios.post(`${LOAN_API_URL}/loans/${loanId}/decision`, { decision });

        return {
            statusCode: response.status,
            body: JSON.stringify(response.data),
        };
    } catch (error) {
        console.error('Error approving or rejecting loan:', error);
        return {
            statusCode: error.response?.status || 500,
            body: JSON.stringify({ message: 'An error occurred while processing the request.' }),
        };
    }
};