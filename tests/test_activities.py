"""
Unit tests for Activity Functions.
"""

import pytest
from shared_utils import (
    approve_loan,
    evaluate_credit_decision,
    perform_fraud_check,
    verify_applicant_info,
)


class TestVerifyApplicantInfo:
    """Tests for verify_applicant_info activity."""
    
    def test_verify_valid_application(self, sample_application_event):
        """Test verification of valid application."""
        result = verify_applicant_info(sample_application_event)
        
        assert result["verified"] is True
        assert result["application_id"] == sample_application_event["application_id"]
        assert result["applicant_name"] == sample_application_event["applicant_name"]
        assert result["loan_amount"] == sample_application_event["loan_amount"]
        assert "verification_timestamp" in result
    
    def test_verify_missing_application_id(self):
        """Test verification fails with missing application_id."""
        event = {
            "applicant_name": "John",
            "loan_amount": 50000,
        }
        
        with pytest.raises(ValueError, match="Missing required fields"):
            verify_applicant_info(event)
    
    def test_verify_missing_applicant_name(self):
        """Test verification fails with missing applicant_name."""
        event = {
            "application_id": "test-001",
            "loan_amount": 50000,
        }
        
        with pytest.raises(ValueError, match="Missing required fields"):
            verify_applicant_info(event)
    
    def test_verify_missing_loan_amount(self):
        """Test verification fails with missing loan_amount."""
        event = {
            "application_id": "test-001",
            "applicant_name": "John",
        }
        
        with pytest.raises(ValueError, match="Missing required fields"):
            verify_applicant_info(event)
    
    def test_verify_multiple_missing_fields(self):
        """Test verification fails with multiple missing fields."""
        event = {"application_id": "test-001"}
        
        with pytest.raises(ValueError) as exc_info:
            verify_applicant_info(event)
        
        assert "Missing required fields" in str(exc_info.value)


class TestPerformFraudCheck:
    """Tests for perform_fraud_check activity."""
    
    def test_fraud_check_pass(self, sample_application_event):
        """Test fraud check passes (default behavior)."""
        verified_data = {**sample_application_event, "verified": True}
        
        result = perform_fraud_check(verified_data)
        
        assert result["fraud_check"] == "passed"
        assert "fraud_check_timestamp" in result
        assert result["application_id"] == sample_application_event["application_id"]
    
    def test_fraud_check_preserves_data(self, sample_application_event):
        """Test fraud check preserves input data."""
        verified_data = {**sample_application_event, "verified": True}
        
        result = perform_fraud_check(verified_data)
        
        assert result["application_id"] == verified_data["application_id"]
        assert result["applicant_name"] == verified_data["applicant_name"]
        assert result["loan_amount"] == verified_data["loan_amount"]


class TestEvaluateCreditDecision:
    """Tests for evaluate_credit_decision activity."""
    
    def test_alice_always_approved(self, alice_event):
        """Test Alice scenario - always approved."""
        verified_data = {**alice_event, "verified": True}
        fraud_data = {**verified_data, "fraud_check": "passed"}
        
        result = evaluate_credit_decision(fraud_data)
        
        assert result["approved"] is True
        assert result["credit_reason"] == "Excellent credit history"
        assert "credit_decision_timestamp" in result
    
    def test_bob_always_denied(self, bob_event):
        """Test Bob scenario - always denied."""
        verified_data = {**bob_event, "verified": True}
        fraud_data = {**verified_data, "fraud_check": "passed"}
        
        with pytest.raises(ValueError, match="Credit decision denied"):
            evaluate_credit_decision(fraud_data)
    
    def test_charlie_approved_low_amount(self, charlie_event):
        """Test Charlie scenario - approved with low loan amount."""
        verified_data = {**charlie_event, "verified": True}
        fraud_data = {**verified_data, "fraud_check": "passed"}
        
        result = evaluate_credit_decision(fraud_data)
        
        assert result["approved"] is True
        assert result["credit_reason"] == "Within credit limit"
    
    def test_charlie_denied_high_amount(self, charlie_high_amount_event):
        """Test Charlie scenario - denied with high loan amount."""
        verified_data = {**charlie_high_amount_event, "verified": True}
        fraud_data = {**verified_data, "fraud_check": "passed"}
        
        with pytest.raises(ValueError, match="Loan amount exceeds limit"):
            evaluate_credit_decision(fraud_data)
    
    def test_default_scenario_approved(self, default_scenario_event):
        """Test default scenario - auto-approved."""
        verified_data = {**default_scenario_event, "verified": True}
        fraud_data = {**verified_data, "fraud_check": "passed"}
        
        result = evaluate_credit_decision(fraud_data)
        
        assert result["approved"] is True
        assert result["credit_reason"] == "Credit check passed"
    
    def test_credit_decision_with_missing_ssn_defaults(self):
        """Test credit decision with missing ssn_last4 defaults."""
        app_data = {
            "application_id": "test-001",
            "applicant_name": "Test",
            "loan_amount": 20000,
            "verified": True,
            "fraud_check": "passed",
        }
        
        result = evaluate_credit_decision(app_data)
        
        # Missing ssn_last4 defaults to "0000" (not in scenarios)
        assert result["approved"] is True


class TestApproveLoan:
    """Tests for approve_loan activity."""
    
    def test_approve_loan_success(self, alice_event):
        """Test loan approval with all data."""
        approval_data = {
            **alice_event,
            "verified": True,
            "fraud_check": "passed",
            "approved": True,
            "credit_reason": "Excellent credit history",
            "credit_decision_timestamp": "2026-03-27T10:00:00+00:00",
        }
        
        result = approve_loan(approval_data)
        
        assert result["status"] == "approved"
        assert result["application_id"] == alice_event["application_id"]
        assert result["applicant_name"] == alice_event["applicant_name"]
        assert result["loan_amount"] == alice_event["loan_amount"]
        assert result["reason"] == "Excellent credit history"
        assert "approval_timestamp" in result
    
    def test_approve_loan_preserves_critical_data(self):
        """Test approval preserves critical application data."""
        app_data = {
            "application_id": "test-123",
            "applicant_name": "Test User",
            "loan_amount": 75000,
            "credit_reason": "Good credit",
        }
        
        result = approve_loan(app_data)
        
        assert result["application_id"] == "test-123"
        assert result["applicant_name"] == "Test User"
        assert result["loan_amount"] == 75000
        assert result["reason"] == "Good credit"


class TestActivityIntegration:
    """Integration tests for activity sequences."""
    
    def test_full_approval_flow_alice(self, alice_event, patched_dynamodb):
        """Test full workflow for Alice (approved)."""
        # Step 1: Verify
        verified = verify_applicant_info(alice_event)
        assert verified["verified"] is True
        
        # Step 2: Fraud Check
        fraud_checked = perform_fraud_check(verified)
        assert fraud_checked["fraud_check"] == "passed"
        
        # Step 3: Credit Decision
        credit_result = evaluate_credit_decision(fraud_checked)
        assert credit_result["approved"] is True
        
        # Step 4: Approve
        approval = approve_loan(credit_result)
        assert approval["status"] == "approved"
    
    def test_approval_flow_stops_at_bob(self, bob_event, patched_dynamodb):
        """Test workflow stops at Bob (denied)."""
        # Step 1: Verify
        verified = verify_applicant_info(bob_event)
        assert verified["verified"] is True
        
        # Step 2: Fraud Check
        fraud_checked = perform_fraud_check(verified)
        assert fraud_checked["fraud_check"] == "passed"
        
        # Step 3: Credit Decision - Should fail
        with pytest.raises(ValueError):
            evaluate_credit_decision(fraud_checked)
    
    def test_approval_flow_charlie_approved(self, charlie_event, patched_dynamodb):
        """Test workflow for Charlie with approved amount."""
        verified = verify_applicant_info(charlie_event)
        fraud_checked = perform_fraud_check(verified)
        credit_result = evaluate_credit_decision(fraud_checked)
        approval = approve_loan(credit_result)
        
        assert approval["status"] == "approved"
        assert credit_result["credit_reason"] == "Within credit limit"
    
    def test_approval_flow_charlie_rejected(self, charlie_high_amount_event, patched_dynamodb):
        """Test workflow for Charlie with high amount."""
        verified = verify_applicant_info(charlie_high_amount_event)
        fraud_checked = perform_fraud_check(verified)
        
        with pytest.raises(ValueError, match="Loan amount exceeds limit"):
            evaluate_credit_decision(fraud_checked)
