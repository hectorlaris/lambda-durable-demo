"""
Shared utilities and Activity Functions for Loan Approval Workflow.
Durable Functions pattern.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from aws_lambda_powertools import Logger

logger = Logger()

# Control DynamoDB operations (disable for testing)
_DYNAMODB_ENABLED = os.environ.get("DYNAMODB_ENABLED", "true").lower() == "true"
_dynamodb_client: Optional[Any] = None
PROGRESS_TABLE = os.environ.get("PROGRESS_TABLE", "loan-progress-v1")


def _get_dynamodb():
    """Lazy load DynamoDB client."""
    global _dynamodb_client
    if _dynamodb_client is None and _DYNAMODB_ENABLED:
        import boto3
        _dynamodb_client = boto3.resource("dynamodb")
    return _dynamodb_client


def log_progress(application_id: str, step: str, message: str, status: str) -> None:
    """Log workflow progress to DynamoDB.
    
    Called by activity functions to record execution progress.
    """
    if not _DYNAMODB_ENABLED:
        logger.info(f"[TEST-MODE] Progress: {step} - {status}")
        return
    
    dynamodb = _get_dynamodb()
    if not dynamodb:
        logger.warning("DynamoDB not available")
        return
    
    table = dynamodb.Table(PROGRESS_TABLE)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    log_entry = {
        "step": step,
        "message": message,
        "level": "info",
        "timestamp": timestamp,
    }
    
    try:
        table.update_item(
            Key={"application_id": application_id},
            UpdateExpression="SET #logs = list_append(if_not_exists(#logs, :empty_list), :log_entry), #status = :status, current_step = :step",
            ExpressionAttributeNames={
                "#logs": "logs",
                "#status": "status",
            },
            ExpressionAttributeValues={
                ":log_entry": [log_entry],
                ":status": status,
                ":step": step,
                ":empty_list": [],
            },
        )
        
        logger.info(
            "Progress logged",
            application_id=application_id,
            step=step,
            status=status,
        )
    except Exception as e:
        logger.warning(f"Failed to log progress: {str(e)}")


def set_final_result(
    application_id: str,
    result: Dict[str, Any],
    final_status: str
) -> None:
    """Set final result and status in DynamoDB."""
    if not _DYNAMODB_ENABLED:
        logger.info(f"[TEST-MODE] Final result: {final_status}")
        return
    
    dynamodb = _get_dynamodb()
    if not dynamodb:
        logger.warning("DynamoDB not available")
        return
    
    table = dynamodb.Table(PROGRESS_TABLE)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    log_entry = {
        "step": "completed",
        "message": f"Application {final_status}: {result.get('reason', '')}",
        "level": "info",
        "timestamp": timestamp,
    }
    
    try:
        table.update_item(
            Key={"application_id": application_id},
            UpdateExpression="SET #logs = list_append(if_not_exists(#logs, :empty_list), :log_entry), #status = :status, #result = :result, current_step = :step",
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
                ":empty_list": [],
            },
        )
        
        logger.info(
            "Final result set",
            application_id=application_id,
            status=final_status,
        )
    except Exception as e:
        logger.warning(f"Failed to set final result: {str(e)}")


# ────────────────────────────────────────────────────────
# Activity Functions (called via yield context.call_activity)
# ────────────────────────────────────────────────────────

def verify_applicant_info(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Activity: Verify applicant information.
    
    Args:
        application_data: Application details from input event
        
    Returns:
        Verified application data
    """
    application_id = application_data.get("application_id")
    logger.info("Verifying applicant information", application_id=application_id)
    
    log_progress(
        application_id,
        "verifying_info",
        "Verifying applicant information",
        "verifying_info"
    )
    
    # Validation logic
    required_fields = ["application_id", "applicant_name", "loan_amount"]
    missing = [f for f in required_fields if f not in application_data]
    
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    
    return {
        **application_data,
        "verified": True,
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def perform_fraud_check(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Activity: Perform fraud detection checks.
    
    Args:
        application_data: Application data from previous step
        
    Returns:
        Data with fraud check results
    """
    application_id = application_data.get("application_id")
    logger.info("Performing fraud check", application_id=application_id)
    
    log_progress(
        application_id,
        "fraud_check_pending",
        "Running fraud detection checks",
        "fraud_check_pending"
    )
    
    # Fraud check logic (simplified)
    fraud_decision = "pass"  # In production: external API call
    
    log_progress(
        application_id,
        "fraud_check_complete",
        "Fraud check passed - no suspicious activity detected",
        "fraud_check_complete"
    )
    
    if fraud_decision == "fail":
        raise ValueError("Fraud check failed")
    
    return {
        **application_data,
        "fraud_check": "passed",
        "fraud_check_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def evaluate_credit_decision(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Activity: Evaluate credit eligibility.
    
    Hardcoded scenarios:
      - SIN ending 1111: Always approved
      - SIN ending 2222: Always denied (credit score too low)
      - SIN ending 3333: Approved if loan_amount <= $25,000
      - Others: Auto-approved
    
    Args:
        application_data: Application data from previous steps
        
    Returns:
        Data with credit decision results
        
    Raises:
        ValueError: If application not approved
    """
    application_id = application_data.get("application_id")
    loan_amount = application_data.get("loan_amount", 0)
    ssn_last4 = str(application_data.get("ssn_last4", "0000"))[-4:]
    
    logger.info(
        "Evaluating credit decision",
        application_id=application_id,
        ssn_last4=ssn_last4,
        loan_amount=loan_amount,
    )
    
    log_progress(
        application_id,
        "credit_decision",
        "Evaluating credit eligibility",
        "credit_decision"
    )
    
    # Credit decision logic
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
        logger.info(
            "Application rejected by credit decision",
            application_id=application_id,
            reason=reason,
        )
        raise ValueError(f"Credit decision denied: {reason}")
    
    return {
        **application_data,
        "approved": True,
        "credit_reason": reason,
        "credit_decision_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def approve_loan(application_data: Dict[str, Any]) -> Dict[str, Any]:
    """Activity: Finalize loan approval.
    
    Args:
        application_data: Fully processed application data
        
    Returns:
        Final approval result
    """
    application_id = application_data.get("application_id")
    applicant_name = application_data.get("applicant_name")
    loan_amount = application_data.get("loan_amount")
    credit_reason = application_data.get("credit_reason", "")
    
    logger.info("Finalizing loan approval", application_id=application_id)
    
    log_progress(
        application_id,
        "approval",
        f"Loan approved for {applicant_name}",
        "approved"
    )
    
    return {
        "application_id": application_id,
        "applicant_name": applicant_name,
        "loan_amount": loan_amount,
        "status": "approved",
        "reason": credit_reason,
        "approval_timestamp": datetime.now(timezone.utc).isoformat(),
    }
