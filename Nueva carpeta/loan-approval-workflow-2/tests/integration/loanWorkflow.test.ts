import { submitLoanApplication } from '../../src/functions/submitLoanApplication/index';
import { evaluateCreditScore } from '../../src/functions/evaluateCreditScore/index';
import { approveOrRejectLoan } from '../../src/functions/approveOrRejectLoan/index';
import { notifyApplicant } from '../../src/functions/notifyApplicant/index';

describe('Loan Workflow Integration Tests', () => {
    it('should submit a loan application and evaluate credit score', async () => {
        const applicationData = {
            applicantId: '12345',
            amount: 10000,
            term: 12,
            // additional fields as necessary
        };

        const submitResponse = await submitLoanApplication(applicationData);
        expect(submitResponse).toHaveProperty('status', 'submitted');

        const creditScoreResponse = await evaluateCreditScore(applicationData.applicantId);
        expect(creditScoreResponse).toHaveProperty('score');
    });

    it('should approve a loan application', async () => {
        const applicationId = '67890';
        const managerDecision = { approved: true };

        const approvalResponse = await approveOrRejectLoan(applicationId, managerDecision);
        expect(approvalResponse).toHaveProperty('status', 'approved');

        const notificationResponse = await notifyApplicant(applicationId);
        expect(notificationResponse).toHaveProperty('message', 'Applicant notified successfully');
    });

    it('should reject a loan application', async () => {
        const applicationId = '54321';
        const managerDecision = { approved: false };

        const rejectionResponse = await approveOrRejectLoan(applicationId, managerDecision);
        expect(rejectionResponse).toHaveProperty('status', 'rejected');

        const notificationResponse = await notifyApplicant(applicationId);
        expect(notificationResponse).toHaveProperty('message', 'Applicant notified successfully');
    });
});