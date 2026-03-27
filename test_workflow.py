#!/usr/bin/env python3
"""
Local testing script for Loan Approval Workflow.
Simulates the orchestrator and activities locally without AWS.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shared_utils import (
    approve_loan,
    evaluate_credit_decision,
    perform_fraud_check,
    set_final_result,
    verify_applicant_info,
)


# ──────────────────────────────────────────────────────
# Test Data
# ──────────────────────────────────────────────────────

TEST_SCENARIOS = {
    "alice": {
        "description": "Alice - Excellent credit - SHOULD APPROVE",
        "event": {
            "application_id": "alice-001",
            "applicant_name": "Alice Johnson",
            "loan_amount": 100000,
            "ssn_last4": "1111",
        },
        "expected_status": "approved",
    },
    "bob": {
        "description": "Bob - Low credit score - SHOULD REJECT",
        "event": {
            "application_id": "bob-001",
            "applicant_name": "Bob Smith",
            "loan_amount": 50000,
            "ssn_last4": "2222",
        },
        "expected_status": "rejected",
    },
    "charlie_low": {
        "description": "Charlie - Within limit ($20K) - SHOULD APPROVE",
        "event": {
            "application_id": "charlie-low-001",
            "applicant_name": "Charlie Brown",
            "loan_amount": 20000,
            "ssn_last4": "3333",
        },
        "expected_status": "approved",
    },
    "charlie_high": {
        "description": "Charlie - Exceeds limit ($50K) - SHOULD REJECT",
        "event": {
            "application_id": "charlie-high-001",
            "applicant_name": "Charlie Brown",
            "loan_amount": 50000,
            "ssn_last4": "3333",
        },
        "expected_status": "rejected",
    },
    "default": {
        "description": "David - Default scenario - SHOULD APPROVE",
        "event": {
            "application_id": "default-001",
            "applicant_name": "David Lee",
            "loan_amount": 30000,
            "ssn_last4": "9999",
        },
        "expected_status": "approved",
    },
}


# ──────────────────────────────────────────────────────
# Orchestrator Simulation
# ──────────────────────────────────────────────────────

class WorkflowSimulator:
    """Simulates the loan workflow locally."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.checkpoints = []
        self.activities_executed = []
    
    def log(self, level: str, message: str):
        """Log with level indicator."""
        if self.verbose or level in ["ERROR", "RESULT"]:
            timestamp = datetime.now(timezone.utc).isoformat()
            print(f"[{timestamp}] [{level}] {message}")
    
    def checkpoint(self, step: str):
        """Record a checkpoint."""
        self.checkpoints.append({
            "step": step,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self.log("CHECKPOINT", f"✓ {step}")
    
    def execute_orchestrator(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the loan orchestrator workflow."""
        app_id = event.get("application_id")
        self.log("INFO", f"▶ Starting workflow for {app_id}")
        
        try:
            # ─── Step 1: Verify Applicant Information ───
            self.log("INFO", "Step 1/4: Verify applicant information...")
            verified = verify_applicant_info(event)
            self.checkpoint("verify_applicant_info")
            self.activities_executed.append("verify_applicant_info")
            
            # ─── Step 2: Perform Fraud Check ───
            self.log("INFO", "Step 2/4: Perform fraud checks...")
            fraud_checked = perform_fraud_check(verified)
            self.checkpoint("perform_fraud_check")
            self.activities_executed.append("perform_fraud_check")
            
            # ─── Step 3: Evaluate Credit Decision ───
            self.log("INFO", "Step 3/4: Evaluate credit eligibility...")
            credit_decided = evaluate_credit_decision(fraud_checked)
            self.checkpoint("evaluate_credit_decision")
            self.activities_executed.append("evaluate_credit_decision")
            
            # ─── Step 4: Approve Loan ───
            self.log("INFO", "Step 4/4: Finalize loan approval...")
            approval = approve_loan(credit_decided)
            self.checkpoint("approve_loan")
            self.activities_executed.append("approve_loan")
            
            # ✓ Success
            self.log("RESULT", f"✓ Workflow completed: {approval['status'].upper()}")
            self.log("RESULT", f"  Reason: {approval.get('reason', 'N/A')}")
            return approval
            
        except Exception as e:
            # ✗ Error - Stop and reject
            error_msg = str(e)
            self.log("ERROR", f"✗ Workflow failed: {error_msg}")
            
            result = {
                "status": "rejected",
                "application_id": app_id,
                "reason": error_msg,
            }
            
            return result
    
    def print_summary(self):
        """Print execution summary."""
        print("\n" + "=" * 70)
        print("EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Activities executed: {' → '.join(self.activities_executed) or 'None'}")
        print(f"Checkpoints created: {len(self.checkpoints)}")
        for i, cp in enumerate(self.checkpoints, 1):
            print(f"  {i}. {cp['step']}")
        print()


# ──────────────────────────────────────────────────────
# Test Runner
# ──────────────────────────────────────────────────────

def run_test(scenario_name: str, scenario_data: Dict[str, Any]) -> bool:
    """Run a single test scenario."""
    print("\n" + "─" * 70)
    print(f"TEST: {scenario_data['description']}")
    print("─" * 70)
    
    event = scenario_data["event"]
    expected = scenario_data["expected_status"]
    
    # Execute
    simulator = WorkflowSimulator(verbose=True)
    result = simulator.execute_orchestrator(event)
    simulator.print_summary()
    
    # Verify
    actual = result.get("status")
    passed = actual == expected
    
    status_icon = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status_icon}: Expected '{expected}', got '{actual}'")
    
    return passed


def run_all_tests() -> bool:
    """Run all test scenarios."""
    print("\n" + "=" * 70)
    print("AWS LAMBDA DURABLE FUNCTIONS - LOAN WORKFLOW LOCAL TESTS")
    print("=" * 70)
    
    results = {}
    
    for scenario_key, scenario_data in TEST_SCENARIOS.items():
        passed = run_test(scenario_key, scenario_data)
        results[scenario_key] = passed
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    for scenario, passed in results.items():
        icon = "✓" if passed else "✗"
        print(f"  {icon} {scenario}: {TEST_SCENARIOS[scenario]['description']}")
    
    print(f"\nTotal: {passed_count}/{total_count} passed")
    print("=" * 70 + "\n")
    
    return passed_count == total_count


def run_retry_simulation():
    """Simulate retry behavior."""
    print("\n" + "=" * 70)
    print("RETRY BEHAVIOR SIMULATION")
    print("=" * 70)
    
    print("""
This demonstrates how Durable Functions would handle retries:

Scenario: Step 3 (Credit Decision) fails

WITHOUT Durable Functions (Monolith):
  ✗ Step 1 Verify → Executed
  ✗ Step 2 Fraud  → Executed
  ✗ Step 3 Credit → FAILED
  
  ON RETRY:
  ✗ Step 1 Verify → RE-EXECUTED (unnecessary)
  ✗ Step 2 Fraud  → RE-EXECUTED (unnecessary)
  ✗ Step 3 Credit → RE-EXECUTED (necessary)

WITH Durable Functions:
  ✓ Step 1 Verify → Executed → CHECKPOINT
  ✓ Step 2 Fraud  → Executed → CHECKPOINT
  ✗ Step 3 Credit → FAILED
  
  ON RETRY (with Replay):
  ✓ Step 1 Verify → REPLAYED (from checkpoint)
  ✓ Step 2 Fraud  → REPLAYED (from checkpoint)
  ✓ Step 3 Credit → RETRIED (with RetryPolicy max=2)

✓ Result: Only failed step is retried - much more efficient!
    """)
    
    print("=" * 70 + "\n")


# ──────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Local testing for Loan Approval Workflow"
    )
    parser.add_argument(
        "--scenario",
        choices=list(TEST_SCENARIOS.keys()),
        help="Run specific scenario",
    )
    parser.add_argument(
        "--retry-demo",
        action="store_true",
        help="Show retry behavior simulation",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output",
    )
    
    args = parser.parse_args()
    
    if args.retry_demo:
        run_retry_simulation()
        return 0
    
    if args.scenario:
        scenario_data = TEST_SCENARIOS[args.scenario]
        passed = run_test(args.scenario, scenario_data)
        return 0 if passed else 1
    
    # Run all tests
    all_passed = run_all_tests()
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
