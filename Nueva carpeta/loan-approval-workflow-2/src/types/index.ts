export interface LoanApplication {
    applicantId: string;
    amountRequested: number;
    purpose: string;
    creditScore: number;
    status?: 'pending' | 'approved' | 'rejected';
}

export interface LoanResponse {
    applicationId: string;
    status: 'approved' | 'rejected';
    message: string;
}

export interface CreditScoreEvaluation {
    applicantId: string;
    creditScore: number;
    isEligible: boolean;
    reason?: string;
}