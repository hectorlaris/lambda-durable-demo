import { SNS } from 'aws-sdk';

const sns = new SNS();

export const notifyApplicant = async (applicantEmail: string, loanStatus: string) => {
    const message = `Your loan application status is: ${loanStatus}`;
    const params = {
        Message: message,
        Subject: 'Loan Application Status',
        TopicArn: process.env.SNS_TOPIC_ARN, // Ensure this environment variable is set
    };

    try {
        await sns.publish(params).promise();
        console.log(`Notification sent to ${applicantEmail}`);
    } catch (error) {
        console.error(`Failed to send notification: ${error.message}`);
        throw new Error('Notification failed');
    }
};