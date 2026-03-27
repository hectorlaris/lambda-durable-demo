"""
Loan Approval Workflow Lambda
=============================

Simple loan processing workflow that updates progress in DynamoDB through each step.

Hardcoded scenarios:
  - SIN ending 1111: Always approved
  - SIN ending 2222: Always denied (credit score too low)
  - SIN ending 3333: Approved if loan_amount <= $25,000
  - Others: Auto-approved
"""

import json
import os
import time
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()

dynamodb = boto3.resource("dynamodb")
PROGRESS_TABLE = os.environ.get("PROGRESS_TABLE", "loan-progress-v1")


def update_progress(application_id, step, message, status):
    """Update DynamoDB with workflow progress."""
    table = dynamodb.Table(PROGRESS_TABLE)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    log_entry = {
        "step": step,
        "message": message,
        "level": "info",
        "timestamp": timestamp,
    }
    
    table.update_item(
        Key={"application_id": application_id},
        UpdateExpression="SET #logs = list_append(#logs, :log_entry), #status = :status, current_step = :step",
        ExpressionAttributeNames={
            "#logs": "logs",
            "#status": "status",
        },
        ExpressionAttributeValues={
            ":log_entry": [log_entry],
            ":status": status,
            ":step": step,
        },
    )
    logger.info(
        "Progress updated",
        application_id=application_id,
        step=step,
        status=status,
    )


def set_result(application_id, result, final_status):
    """Set final result and status."""
    table = dynamodb.Table(PROGRESS_TABLE)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    log_entry = {
        "step": "completed",
        "message": f"Application {final_status}: {result.get('reason', '')}",
        "level": "info",
        "timestamp": timestamp,
    }
    
    table.update_item(
        Key={"application_id": application_id},
        UpdateExpression="SET #logs = list_append(#logs, :log_entry), #status = :status, #result = :result, current_step = :step",
        ExpressionAttributeNames={
            "#logs": "logs",
            "#status": "status",
            "#result": "result",
        },
        ExpressionAttributeValues={
            ":log_entry": [log_entry],
            ":status": final_status,
            ":result": json.dumps(result),
            ":step": "completed",
        },
    )


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    """Main workflow handler."""
    logger.info("Workflow started", event=event)
    
    application_id = event.get("application_id")
    applicant_name = event.get("applicant_name")
    loan_amount = event.get("loan_amount", 0)
    ssn_last4 = event.get("ssn_last4", "0000")[-4:]  # Get last 4 digits
    
    if not application_id:
        logger.error("Missing application_id")
        return {"status": "error", "message": "Missing application_id"}
    
    try:
        # Step 1: Processing
        logger.info("Processing application", application_id=application_id)
        update_progress(application_id, "processing", "Verifying applicant information", "processing")
        time.sleep(2)  # Simulate processing
        
        # Step 2: Fraud Check
        logger.info("Starting fraud check", application_id=application_id)
        update_progress(application_id, "fraud_check_pending", "Running fraud detection checks", "fraud_check_pending")
        time.sleep(2)  # Simulate fraud check
        
        fraud_decision = "pass"  # Assume fraud check passes
        fraud_message = "Fraud check passed - no suspicious activity detected"
        update_progress(application_id, "fraud_check_complete", fraud_message, "fraud_check_complete")
        
        if fraud_decision == "fail":
            set_result(
                application_id,
                {"reason": "Fraud check failed"},
                "rejected"
            )
            return {"status": "rejected", "message": "Fraud check failed"}
        
        # Step 3: Credit Decision (based on hardcoded scenarios)
        logger.info("Running credit decision", application_id=application_id)
        update_progress(application_id, "credit_decision", "Evaluating credit eligibility", "credit_decision")
        time.sleep(2)  # Simulate credit decision
        
        approved = False
        reason = ""
        
        if ssn_last4 == "1111":  # Alice scenario
            approved = True
            reason = "Excellent credit history"
        elif ssn_last4 == "2222":  # Bob scenario
            approved = False
            reason = "Credit score too low"
        elif ssn_last4 == "3333":  # Charlie scenario
            approved = loan_amount <= 25000
            reason = "Loan amount exceeds limit" if not approved else "Within credit limit"
        else:  # Default
            approved = True
            reason = "Credit check passed"
        
        if not approved:
            set_result(
                application_id,
                {"reason": reason},
                "rejected"
            )
            logger.info(
                "Application rejected",
                application_id=application_id,
                reason=reason,
            )
            return {"status": "rejected", "reason": reason}
        
        # Step 4: Approval
        logger.info("Application approved", application_id=application_id)
        set_result(
            application_id,
            {
                "reason": reason,
                "loan_amount": loan_amount,
                "applicant_name": applicant_name,
            },
            "approved"
        )
        
        return {
            "status": "approved",
            "application_id": application_id,
            "message": reason,
        }
        
    except Exception as e:
        logger.exception(
            "Workflow error",
            application_id=application_id,
            error=str(e),
        )
        set_result(
            application_id,
            {"error": str(e)},
            "error"
        )
        raise
