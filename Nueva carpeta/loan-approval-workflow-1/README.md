# Loan Approval Workflow

This project implements a loan approval workflow using AWS Lambda, with a frontend API layer and a DynamoDB backend. The workflow allows users to submit loan applications, evaluate credit scores, approve or reject loans, and notify applicants of their application status.

## Project Structure

```
loan-approval-workflow
├── src
│   ├── functions
│   │   ├── submitLoanApplication
│   │   │   └── index.ts
│   │   ├── evaluateCreditScore
│   │   │   └── index.ts
│   │   ├── approveOrRejectLoan
│   │   │   └── index.ts
│   │   └── notifyApplicant
│   │       └── index.ts
│   ├── api
│   │   ├── routes
│   │   │   └── loanRoutes.ts
│   │   └── middleware
│   │       └── authMiddleware.ts
│   ├── db
│   │   ├── dynamoClient.ts
│   │   └── loanRepository.ts
│   └── types
│       └── index.ts
├── infra
│   ├── template.yaml
│   └── parameters.json
├── tests
│   ├── unit
│   │   ├── evaluateCreditScore.test.ts
│   │   ├── approveOrRejectLoan.test.ts
│   │   └── loanRepository.test.ts
│   └── integration
│       └── loanWorkflow.test.ts
├── package.json
├── tsconfig.json
├── samconfig.toml
└── README.md
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd loan-approval-workflow
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Configure AWS Credentials**
   Ensure that your AWS credentials are configured properly to allow access to the necessary services.

4. **Deploy the Application**
   Use the AWS SAM CLI to build and deploy the application:
   ```bash
   sam build
   sam deploy --guided
   ```

## API Endpoints

- **POST /loan/apply**: Submit a loan application.
- **GET /loan/status/{id}**: Check the status of a loan application.
- **POST /loan/approve**: Approve a loan application.
- **POST /loan/reject**: Reject a loan application.

## Testing

To run the unit tests, use the following command:
```bash
npm test
```

For integration tests, ensure that the application is deployed and run:
```bash
npm run test:integration
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.