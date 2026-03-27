import { Router } from 'express';
import { submitLoanApplication } from '../../functions/submitLoanApplication/index';
import { evaluateCreditScore } from '../../functions/evaluateCreditScore/index';
import { approveOrRejectLoan } from '../../functions/approveOrRejectLoan/index';
import { notifyApplicant } from '../../functions/notifyApplicant/index';
import { authMiddleware } from '../middleware/authMiddleware';

const loanRoutes = Router();

loanRoutes.post('/apply', authMiddleware, submitLoanApplication);
loanRoutes.get('/credit-score', authMiddleware, evaluateCreditScore);
loanRoutes.post('/approve', authMiddleware, approveOrRejectLoan);
loanRoutes.post('/notify', authMiddleware, notifyApplicant);

export default loanRoutes;