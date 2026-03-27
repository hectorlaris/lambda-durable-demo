"""
Test fixtures and mock utilities for Loan Workflow testing.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ──────────────────────────────────────────────────────
# Mock DynamoDB
# ──────────────────────────────────────────────────────

class MockDynamoDBTable:
    """Mock DynamoDB Table for testing."""
    
    def __init__(self):
        self.items = {}
    
    def update_item(self, Key, UpdateExpression, ExpressionAttributeNames, 
                   ExpressionAttributeValues):
        """Mock update_item for progress logging."""
        app_id = Key["application_id"]
        
        if app_id not in self.items:
            self.items[app_id] = {
                "application_id": app_id,
                "logs": [],
                "status": None,
                "result": None,
            }
        
        item = self.items[app_id]
        
        # Handle logs list_append
        if "#logs" in ExpressionAttributeNames:
            if ":log_entry" in ExpressionAttributeValues:
                log_entry = ExpressionAttributeValues[":log_entry"][0]
                item["logs"].append(log_entry)
        
        # Handle status update
        if "#status" in ExpressionAttributeNames:
            if ":status" in ExpressionAttributeValues:
                item["status"] = ExpressionAttributeValues[":status"]
        
        # Handle result update
        if "#result" in ExpressionAttributeNames:
            if ":result" in ExpressionAttributeValues:
                item["result"] = ExpressionAttributeValues[":result"]
    
    def get_item(self, Key):
        """Mock get_item."""
        app_id = Key["application_id"]
        if app_id in self.items:
            return {"Item": self.items[app_id]}
        return {}


class MockDynamoDBResource:
    """Mock DynamoDB Resource."""
    
    def __init__(self):
        self.tables = {}
    
    def Table(self, table_name: str) -> MockDynamoDBTable:
        """Get or create mock table."""
        if table_name not in self.tables:
            self.tables[table_name] = MockDynamoDBTable()
        return self.tables[table_name]


# ──────────────────────────────────────────────────────
# Mock DurableContext
# ──────────────────────────────────────────────────────

class MockRetryPolicy:
    """Mock RetryPolicy."""
    
    def __init__(self, max_attempts=3):
        self.max_attempts = max_attempts
        self.attempt_count = 0


class MockDurableContext:
    """Mock Durable Context for testing."""
    
    def __init__(self):
        self.activities = {}
        self.call_history = []
        self.checkpoints = []
    
    def call_activity(self, activity_name, **kwargs):
        """Mock call_activity with retry support."""
        self.call_history.append({
            "activity": activity_name,
            "kwargs": kwargs,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        # Record a checkpoint
        self.checkpoints.append({
            "step": activity_name,
            "type": "checkpoint",
        })
        
        # Get activity result
        if activity_name in self.activities:
            activity_func = self.activities[activity_name]
            app_data = kwargs.get("application_data")
            return activity_func(app_data)
        
        raise ValueError(f"Activity {activity_name} not registered")
    
    def register_activity(self, activity_name, activity_func):
        """Register an activity function."""
        self.activities[activity_name] = activity_func


# ──────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────

@pytest.fixture
def mock_dynamodb():
    """Provide mock DynamoDB resource."""
    return MockDynamoDBResource()


@pytest.fixture
def mock_durable_context():
    """Provide mock Durable Context."""
    return MockDurableContext()


@pytest.fixture
def sample_application_event():
    """Sample application event."""
    return {
        "application_id": "test-app-001",
        "applicant_name": "John Doe",
        "loan_amount": 50000,
        "ssn_last4": "1234",
    }


@pytest.fixture
def alice_event():
    """Alice scenario - Always approved."""
    return {
        "application_id": "alice-001",
        "applicant_name": "Alice",
        "loan_amount": 100000,
        "ssn_last4": "1111",
    }


@pytest.fixture
def bob_event():
    """Bob scenario - Always denied."""
    return {
        "application_id": "bob-001",
        "applicant_name": "Bob",
        "loan_amount": 50000,
        "ssn_last4": "2222",
    }


@pytest.fixture
def charlie_event():
    """Charlie scenario - Approved if <= $25,000."""
    return {
        "application_id": "charlie-001",
        "applicant_name": "Charlie",
        "loan_amount": 20000,
        "ssn_last4": "3333",
    }


@pytest.fixture
def charlie_high_amount_event():
    """Charlie scenario with high amount - Denied."""
    return {
        "application_id": "charlie-high-001",
        "applicant_name": "Charlie",
        "loan_amount": 50000,
        "ssn_last4": "3333",
    }


@pytest.fixture
def default_scenario_event():
    """Default scenario - Auto-approved."""
    return {
        "application_id": "default-001",
        "applicant_name": "David",
        "loan_amount": 30000,
        "ssn_last4": "9999",
    }


@pytest.fixture
def patched_dynamodb(mock_dynamodb):
    """Patch boto3.resource to use mock DynamoDB."""
    with patch("boto3.resource") as mock_boto3:
        mock_boto3.return_value = mock_dynamodb
        yield mock_dynamodb


# ──────────────────────────────────────────────────────
# Lambda Context Mock
# ──────────────────────────────────────────────────────

class MockLambdaContext:
    """Mock AWS Lambda Context."""
    
    def __init__(self):
        self.function_name = "LoanWorkflowFunction"
        self.function_version = "$LATEST"
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:LoanWorkflowFunction"
        self.memory_limit_in_mb = 1024
        self.aws_request_id = "test-request-id-123"
        self.log_group_name = "/aws/lambda/LoanWorkflowFunction"
        self.log_stream_name = "2026/03/27/[$LATEST]abcdefg"
        self.identity = None
        self.client_context = None
        self.timeout_in_seconds = 300
    
    def get_remaining_time_in_millis(self) -> int:
        """Get remaining time."""
        return self.timeout_in_seconds * 1000


@pytest.fixture
def lambda_context():
    """Provide mock Lambda Context."""
    return MockLambdaContext()
