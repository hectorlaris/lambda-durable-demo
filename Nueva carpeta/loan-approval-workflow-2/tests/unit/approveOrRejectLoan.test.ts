import { approveOrRejectLoan } from '../../src/functions/approveOrRejectLoan/index';
import { APIGatewayProxyEvent, Context } from 'aws-lambda';

describe('approveOrRejectLoan', () => {
    it('should approve a loan application', async () => {
        const event: APIGatewayProxyEvent = {
            body: JSON.stringify({ loanId: '123', decision: 'approve' }),
            // other necessary properties for the event
        } as any;

        const context: Context = {} as any;

        const response = await approveOrRejectLoan(event, context);

        expect(response.statusCode).toBe(200);
        expect(JSON.parse(response.body).message).toBe('Loan application approved');
    });

    it('should reject a loan application', async () => {
        const event: APIGatewayProxyEvent = {
            body: JSON.stringify({ loanId: '123', decision: 'reject' }),
            // other necessary properties for the event
        } as any;

        const context: Context = {} as any;

        const response = await approveOrRejectLoan(event, context);

        expect(response.statusCode).toBe(200);
        expect(JSON.parse(response.body).message).toBe('Loan application rejected');
    });

    it('should return an error for invalid decision', async () => {
        const event: APIGatewayProxyEvent = {
            body: JSON.stringify({ loanId: '123', decision: 'invalid' }),
            // other necessary properties for the event
        } as any;

        const context: Context = {} as any;

        const response = await approveOrRejectLoan(event, context);

        expect(response.statusCode).toBe(400);
        expect(JSON.parse(response.body).message).toBe('Invalid decision');
    });
});