"""
Integration tests for the Loan Orchestrator (Durable Function).
Tests the full durable function orchestration.
"""

from unittest.mock import patch, MagicMock
import pytest

from shared_utils import (
    approve_loan,
    evaluate_credit_decision,
    perform_fraud_check,
    verify_applicant_info,
)


class TestOrchestratorFlow:
    """Tests for loan_orchestrator function flow."""
    
    def test_orchestrator_alice_approved(self, alice_event, mock_durable_context, patched_dynamodb):
        """Test orchestrator with Alice scenario (approved)."""
        # Register all activities
        mock_durable_context.register_activity(
            "verify_applicant_info",
            verify_applicant_info
        )
        mock_durable_context.register_activity(
            "perform_fraud_check",
            perform_fraud_check
        )
        mock_durable_context.register_activity(
            "evaluate_credit_decision",
            evaluate_credit_decision
        )
        mock_durable_context.register_activity(
            "approve_loan",
            approve_loan
        )
        
        # Simulate orchestrator flow
        verified = mock_durable_context.call_activity(
            "verify_applicant_info",
            application_data=alice_event,
        )
        assert verified["verified"] is True
        
        fraud_checked = mock_durable_context.call_activity(
            "perform_fraud_check",
            application_data=verified,
        )
        assert fraud_checked["fraud_check"] == "passed"
        
        credit_result = mock_durable_context.call_activity(
            "evaluate_credit_decision",
            application_data=fraud_checked,
        )
        assert credit_result["approved"] is True
        
        approval = mock_durable_context.call_activity(
            "approve_loan",
            application_data=credit_result,
        )
        assert approval["status"] == "approved"
        
        # Verify checkpoints were created
        assert len(mock_durable_context.checkpoints) == 4
        assert mock_durable_context.checkpoints[0]["step"] == "verify_applicant_info"
        assert mock_durable_context.checkpoints[1]["step"] == "perform_fraud_check"
        assert mock_durable_context.checkpoints[2]["step"] == "evaluate_credit_decision"
        assert mock_durable_context.checkpoints[3]["step"] == "approve_loan"
    
    def test_orchestrator_bob_rejected(self, bob_event, mock_durable_context, patched_dynamodb):
        """Test orchestrator with Bob scenario (rejected)."""
        mock_durable_context.register_activity(
            "verify_applicant_info",
            verify_applicant_info
        )
        mock_durable_context.register_activity(
            "perform_fraud_check",
            perform_fraud_check
        )
        mock_durable_context.register_activity(
            "evaluate_credit_decision",
            evaluate_credit_decision
        )
        
        verified = mock_durable_context.call_activity(
            "verify_applicant_info",
            application_data=bob_event,
        )
        
        fraud_checked = mock_durable_context.call_activity(
            "perform_fraud_check",
            application_data=verified,
        )
        
        # Credit decision should fail for Bob
        with pytest.raises(ValueError, match="Credit decision denied"):
            mock_durable_context.call_activity(
                "evaluate_credit_decision",
                application_data=fraud_checked,
            )
        
        # Verify we reached the third checkpoint before error
        assert len(mock_durable_context.checkpoints) == 3
    
    def test_orchestrator_all_activities_recorded(self, alice_event, mock_durable_context):
        """Test that all activity calls are recorded."""
        mock_durable_context.register_activity(
            "verify_applicant_info",
            verify_applicant_info
        )
        mock_durable_context.register_activity(
            "perform_fraud_check",
            perform_fraud_check
        )
        mock_durable_context.register_activity(
            "evaluate_credit_decision",
            evaluate_credit_decision
        )
        mock_durable_context.register_activity(
            "approve_loan",
            approve_loan
        )
        
        # Execute full flow
        verified = mock_durable_context.call_activity(
            "verify_applicant_info",
            application_data=alice_event,
        )
        
        fraud_checked = mock_durable_context.call_activity(
            "perform_fraud_check",
            application_data=verified,
        )
        
        credit_result = mock_durable_context.call_activity(
            "evaluate_credit_decision",
            application_data=fraud_checked,
        )
        
        approval = mock_durable_context.call_activity(
            "approve_loan",
            application_data=credit_result,
        )
        
        # Verify call history
        assert len(mock_durable_context.call_history) == 4
        assert mock_durable_context.call_history[0]["activity"] == "verify_applicant_info"
        assert mock_durable_context.call_history[1]["activity"] == "perform_fraud_check"
        assert mock_durable_context.call_history[2]["activity"] == "evaluate_credit_decision"
        assert mock_durable_context.call_history[3]["activity"] == "approve_loan"
    
    def test_orchestrator_with_retry_policy_metadata(self, alice_event, mock_durable_context):
        """Test that retry policy metadata is preserved."""
        mock_durable_context.register_activity(
            "verify_applicant_info",
            verify_applicant_info
        )
        
        # Call activity with retry policy metadata
        result = mock_durable_context.call_activity(
            "verify_applicant_info",
            application_data=alice_event,
            retry_policy=MagicMock(max_attempts=3),
        )
        
        # Verify call was recorded with retry metadata
        assert len(mock_durable_context.call_history) == 1
        call = mock_durable_context.call_history[0]
        assert "retry_policy" in call["kwargs"]
        assert call["kwargs"]["retry_policy"].max_attempts == 3


class TestOrchestratorScenarios:
    """Test orchestrator with all business scenarios."""
    
    def test_scenario_alice_excellent_credit(self, alice_event, mock_durable_context):
        """Scenario: Alice - Excellent credit - APPROVED."""
        mock_durable_context.register_activity(
            "verify_applicant_info", verify_applicant_info
        )
        mock_durable_context.register_activity(
            "perform_fraud_check", perform_fraud_check
        )
        mock_durable_context.register_activity(
            "evaluate_credit_decision", evaluate_credit_decision
        )
        mock_durable_context.register_activity(
            "approve_loan", approve_loan
        )
        
        verified = mock_durable_context.call_activity(
            "verify_applicant_info", application_data=alice_event
        )
        fraud = mock_durable_context.call_activity(
            "perform_fraud_check", application_data=verified
        )
        credit = mock_durable_context.call_activity(
            "evaluate_credit_decision", application_data=fraud
        )
        result = mock_durable_context.call_activity(
            "approve_loan", application_data=credit
        )
        
        assert result["status"] == "approved"
        assert result["reason"] == "Excellent credit history"
    
    def test_scenario_bob_low_credit_score(self, bob_event, mock_durable_context):
        """Scenario: Bob - Low credit score - REJECTED."""
        mock_durable_context.register_activity(
            "verify_applicant_info", verify_applicant_info
        )
        mock_durable_context.register_activity(
            "perform_fraud_check", perform_fraud_check
        )
        mock_durable_context.register_activity(
            "evaluate_credit_decision", evaluate_credit_decision
        )
        
        verified = mock_durable_context.call_activity(
            "verify_applicant_info", application_data=bob_event
        )
        fraud = mock_durable_context.call_activity(
            "perform_fraud_check", application_data=verified
        )
        
        with pytest.raises(ValueError) as exc:
            mock_durable_context.call_activity(
                "evaluate_credit_decision", application_data=fraud
            )
        
        assert "Credit score too low" in str(exc.value)
    
    def test_scenario_charlie_within_limit(self, charlie_event, mock_durable_context):
        """Scenario: Charlie - Within credit limit - APPROVED."""
        mock_durable_context.register_activity(
            "verify_applicant_info", verify_applicant_info
        )
        mock_durable_context.register_activity(
            "perform_fraud_check", perform_fraud_check
        )
        mock_durable_context.register_activity(
            "evaluate_credit_decision", evaluate_credit_decision
        )
        mock_durable_context.register_activity(
            "approve_loan", approve_loan
        )
        
        verified = mock_durable_context.call_activity(
            "verify_applicant_info", application_data=charlie_event
        )
        fraud = mock_durable_context.call_activity(
            "perform_fraud_check", application_data=verified
        )
        credit = mock_durable_context.call_activity(
            "evaluate_credit_decision", application_data=fraud
        )
        result = mock_durable_context.call_activity(
            "approve_loan", application_data=credit
        )
        
        assert result["status"] == "approved"
        assert result["reason"] == "Within credit limit"
    
    def test_scenario_charlie_exceeds_limit(self, charlie_high_amount_event, mock_durable_context):
        """Scenario: Charlie - Exceeds credit limit - REJECTED."""
        mock_durable_context.register_activity(
            "verify_applicant_info", verify_applicant_info
        )
        mock_durable_context.register_activity(
            "perform_fraud_check", perform_fraud_check
        )
        mock_durable_context.register_activity(
            "evaluate_credit_decision", evaluate_credit_decision
        )
        
        verified = mock_durable_context.call_activity(
            "verify_applicant_info", application_data=charlie_high_amount_event
        )
        fraud = mock_durable_context.call_activity(
            "perform_fraud_check", application_data=verified
        )
        
        with pytest.raises(ValueError) as exc:
            mock_durable_context.call_activity(
                "evaluate_credit_decision", application_data=fraud
            )
        
        assert "Loan amount exceeds limit" in str(exc.value)
    
    def test_scenario_default_auto_approved(self, default_scenario_event, mock_durable_context):
        """Scenario: Default - Auto-approved - APPROVED."""
        mock_durable_context.register_activity(
            "verify_applicant_info", verify_applicant_info
        )
        mock_durable_context.register_activity(
            "perform_fraud_check", perform_fraud_check
        )
        mock_durable_context.register_activity(
            "evaluate_credit_decision", evaluate_credit_decision
        )
        mock_durable_context.register_activity(
            "approve_loan", approve_loan
        )
        
        verified = mock_durable_context.call_activity(
            "verify_applicant_info", application_data=default_scenario_event
        )
        fraud = mock_durable_context.call_activity(
            "perform_fraud_check", application_data=verified
        )
        credit = mock_durable_context.call_activity(
            "evaluate_credit_decision", application_data=fraud
        )
        result = mock_durable_context.call_activity(
            "approve_loan", application_data=credit
        )
        
        assert result["status"] == "approved"
        assert result["reason"] == "Credit check passed"


class TestOrchestratorErrorHandling:
    """Test error handling in orchestrator."""
    
    def test_orchestrator_stops_on_verification_error(self, mock_durable_context):
        """Test orchestrator stops if verification fails."""
        mock_durable_context.register_activity(
            "verify_applicant_info", verify_applicant_info
        )
        
        invalid_event = {"application_id": "test"}  # Missing required fields
        
        with pytest.raises(ValueError, match="Missing required fields"):
            mock_durable_context.call_activity(
                "verify_applicant_info",
                application_data=invalid_event,
            )
        
        # Only one checkpoint was created (failed)
        assert len(mock_durable_context.checkpoints) == 1
    
    def test_orchestrator_stops_on_credit_decision_error(self, bob_event, mock_durable_context):
        """Test orchestrator stops if credit decision fails."""
        mock_durable_context.register_activity(
            "verify_applicant_info", verify_applicant_info
        )
        mock_durable_context.register_activity(
            "perform_fraud_check", perform_fraud_check
        )
        mock_durable_context.register_activity(
            "evaluate_credit_decision", evaluate_credit_decision
        )
        
        verified = mock_durable_context.call_activity(
            "verify_applicant_info", application_data=bob_event
        )
        fraud = mock_durable_context.call_activity(
            "perform_fraud_check", application_data=verified
        )
        
        with pytest.raises(ValueError):
            mock_durable_context.call_activity(
                "evaluate_credit_decision", application_data=fraud
            )
        
        # Three checkpoints created (failed at third)
        assert len(mock_durable_context.checkpoints) == 3
        assert mock_durable_context.checkpoints[-1]["step"] == "evaluate_credit_decision"
