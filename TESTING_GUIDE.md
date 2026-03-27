# Testing Guide - Loan Approval Workflow

Complete testing suite for AWS Lambda Durable Functions implementation.

## Overview

The testing suite covers:
- **Unit Tests** - Individual activity functions
- **Integration Tests** - Orchestrator workflow
- **Business Scenarios** - All credit decision scenarios (Alice, Bob, Charlie, Default)
- **Error Handling** - Validation failures and rejections
- **Retry Simulation** - Durable Functions checkpoint/replay behavior

## Quick Start

### 1. Install Dependencies

```bash
# Production dependencies
cd src
pip install -r requirements.txt

# Development dependencies (testing)
cd ..
pip install -r requirements-dev.txt
```

### 2. Run Local Workflow Simulation

```bash
# Run all scenarios
python test_workflow.py

# Run specific scenario
python test_workflow.py --scenario alice
python test_workflow.py --scenario bob
python test_workflow.py --scenario charlie_low
python test_workflow.py --scenario charlie_high
python test_workflow.py --scenario default

# Show retry behavior explanation
python test_workflow.py --retry-demo

# Quiet mode (minimal output)
python test_workflow.py --quiet
```

### 3. Run Full Test Suite (pytest)

```bash
# All tests
pytest

# Verbose output
pytest -v

# With coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_activities.py
pytest tests/test_orchestrator.py

# Run specific test class
pytest tests/test_activities.py::TestVerifyApplicantInfo

# Run specific test
pytest tests/test_activities.py::TestVerifyApplicantInfo::test_verify_valid_application
```

## Test Structure

```
tests/
├── __init__.py                 # Package marker
├── conftest.py                 # Fixtures and mocks
├── test_activities.py          # Unit tests for activities
└── test_orchestrator.py        # Integration tests

test_workflow.py                # Local simulation script
pytest.ini                      # Pytest configuration
requirements-dev.txt            # Test dependencies
```

## Test Files

### conftest.py - Fixtures and Mocks

Provides:
- `MockDynamoDBTable` - In-memory DynamoDB mock
- `MockDurableContext` - Mock Durable Functions context
- `MockLambdaContext` - Mock Lambda context
- Pytest fixtures for all test scenarios

**Key Fixtures:**
```python
@pytest.fixture
def alice_event():
    """Alice scenario - Always approved."""
    return {...}

@pytest.fixture
def mock_dynamodb():
    """In-memory DynamoDB mock."""
    
@pytest.fixture
def mock_durable_context():
    """Mock DurableContext for testing."""
```

### test_activities.py - Unit Tests

Tests individual activity functions:

**TestVerifyApplicantInfo**
- ✓ Valid application verification
- ✓ Missing field validation
- ✓ Multiple missing fields

**TestPerformFraudCheck**
- ✓ Fraud check passes
- ✓ Data preservation

**TestEvaluateCreditDecision**
- ✓ Alice scenario (always approved)
- ✓ Bob scenario (always denied)
- ✓ Charlie low amount (approved)
- ✓ Charlie high amount (denied)
- ✓ Default scenario (auto-approved)

**TestApproveLoan**
- ✓ Successful approval
- ✓ Data preservation

**TestActivityIntegration**
- ✓ Full approval flow (Alice)
- ✓ Workflow stops at rejection (Bob)
- ✓ Conditional approval (Charlie)

### test_orchestrator.py - Integration Tests

Tests the durable orchestrator pattern:

**TestOrchestratorFlow**
- ✓ Alice approved with checkpoints
- ✓ Bob rejected at step 3
- ✓ All activities recorded
- ✓ Retry policy metadata preserved

**TestOrchestratorScenarios**
- ✓ Alice - Excellent credit
- ✓ Bob - Low credit score
- ✓ Charlie - Within limit
- ✓ Charlie - Exceeds limit
- ✓ Default - Auto-approved

**TestOrchestratorErrorHandling**
- ✓ Stops on verification error
- ✓ Stops on credit decision error

## Test Scenarios

### Alice (SIN 1111)
```json
{
  "application_id": "alice-001",
  "applicant_name": "Alice",
  "loan_amount": 100000,
  "ssn_last4": "1111"
}
```
**Expected:** ✓ APPROVED (Excellent credit history)

### Bob (SIN 2222)
```json
{
  "application_id": "bob-001",
  "applicant_name": "Bob",
  "loan_amount": 50000,
  "ssn_last4": "2222"
}
```
**Expected:** ✗ REJECTED (Credit score too low)

### Charlie (SIN 3333) - Low Amount
```json
{
  "application_id": "charlie-low-001",
  "applicant_name": "Charlie",
  "loan_amount": 20000,
  "ssn_last4": "3333"
}
```
**Expected:** ✓ APPROVED ($20K ≤ $25K limit)

### Charlie (SIN 3333) - High Amount
```json
{
  "application_id": "charlie-high-001",
  "applicant_name": "Charlie",
  "loan_amount": 50000,
  "ssn_last4": "3333"
}
```
**Expected:** ✗ REJECTED ($50K > $25K limit)

### Default (SIN 9999)
```json
{
  "application_id": "default-001",
  "applicant_name": "David",
  "loan_amount": 30000,
  "ssn_last4": "9999"
}
```
**Expected:** ✓ APPROVED (Auto-approved)

## Running Tests Locally

### Option 1: Workflow Simulation Script

Most user-friendly for quick testing:

```bash
# Run all scenarios with detailed output
python test_workflow.py

# Expected output:
# ────────────────────────────────────────────────────────
# TEST: Alice - Excellent credit - SHOULD APPROVE
# ────────────────────────────────────────────────────────
# [timestamp] [INFO] ▶ Starting workflow for alice-001
# [timestamp] [INFO] Step 1/4: Verify applicant information...
# [timestamp] [CHECKPOINT] ✓ verify_applicant_info
# [timestamp] [INFO] Step 2/4: Perform fraud checks...
# [timestamp] [CHECKPOINT] ✓ perform_fraud_check
# [timestamp] [INFO] Step 3/4: Evaluate credit eligibility...
# [timestamp] [CHECKPOINT] ✓ evaluate_credit_decision
# [timestamp] [INFO] Step 4/4: Finalize loan approval...
# [timestamp] [CHECKPOINT] ✓ approve_loan
# [timestamp] [RESULT] ✓ Workflow completed: APPROVED
# [timestamp] [RESULT]   Reason: Excellent credit history
# ✓ PASS: Expected 'approved', got 'approved'
```

### Option 2: Pytest

Full test suite with coverage:

```bash
# Basic run
pytest

# Verbose with coverage
pytest -v --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Coverage

Current coverage targets:
- **Activities**: 95%+ (all functions, edge cases)
- **Orchestrator**: 90%+ (flow, retries, errors)
- **Error Handling**: 100% (all failure paths)
- **Scenarios**: 100% (all business rules)

To generate coverage report:
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Checkpoint/Replay Simulation

The mock `DurableContext` simulates checkpoints:

```python
# Each call_activity creates a checkpoint
verified = context.call_activity("verify_applicant_info", ...)
# ✓ Checkpoint 1 created

fraud = context.call_activity("perform_fraud_check", ...)
# ✓ Checkpoint 2 created
# If error here: Checkpoint 1 replayed, Checkpoint 2 retried

credit = context.call_activity("evaluate_credit_decision", ...)
# ✓ Checkpoint 3 created
```

View checkpoints in test output:
```
Checkpoints created: 4
  1. verify_applicant_info
  2. perform_fraud_check
  3. evaluate_credit_decision
  4. approve_loan
```

## Error Scenarios

### Missing Required Fields
```python
event = {"application_id": "test"}  # Missing applicant_name, loan_amount

# Test
pytest tests/test_activities.py::TestVerifyApplicantInfo::test_verify_missing_applicant_name
# Result: ✗ REJECTED (ValueError raised)
```

### Credit Rejection (Bob)
```python
event = {
    "application_id": "bob-001",
    "applicant_name": "Bob",
    "loan_amount": 50000,
    "ssn_last4": "2222"
}

# Test
pytest tests/test_orchestrator.py::TestOrchestratorScenarios::test_scenario_bob_low_credit_score
# Result: ✗ REJECTED (ValueError: Credit decision denied)
```

### Invalid Loan Amount (Charlie)
```python
event = {
    "application_id": "charlie-001",
    "applicant_name": "Charlie",
    "loan_amount": 50000,
    "ssn_last4": "3333"
}

# Test
pytest tests/test_orchestrator.py::TestOrchestratorScenarios::test_scenario_charlie_exceeds_limit
# Result: ✗ REJECTED (ValueError: Loan amount exceeds limit)
```

## Mocking Strategy

### Mock DynamoDB
```python
@pytest.fixture
def mock_dynamodb():
    return MockDynamoDBResource()

def test_something(patched_dynamodb):
    # DynamoDB calls are mocked in-memory
```

### Mock Durable Context
```python
@pytest.fixture
def mock_durable_context():
    context = MockDurableContext()
    context.register_activity("verify_applicant_info", verify_applicant_info)
    return context

def test_orchestrator(mock_durable_context):
    result = mock_durable_context.call_activity(...)
    assert len(mock_durable_context.checkpoints) == 1
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Troubleshooting

### Import Errors
```
ModuleNotFoundError: No module named 'shared_utils'
```
**Solution:** Ensure `tests/` can access `src/`:
```python
# In conftest.py or test file
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

### DynamoDB Connection Errors
```
botocore.exceptions.ClientError: (MockHTTPConnection)
```
**Solution:** Use the `patched_dynamodb` fixture to mock:
```python
def test_something(patched_dynamodb):
    # Automatically mocks boto3.resource("dynamodb")
```

### Missing Fixtures
```
fixture 'mock_durable_context' not found
```
**Solution:** Ensure `conftest.py` is in the `tests/` directory and imported.

## Next Steps

1. ✅ **Unit Tests** - Run `pytest tests/test_activities.py`
2. ✅ **Integration Tests** - Run `pytest tests/test_orchestrator.py`
3. ✅ **Local Simulation** - Run `python test_workflow.py`
4. **Deploy to AWS** - Use SAM CLI:
   ```bash
   sam build
   sam deploy --guided
   ```
5. **Cloud Testing** - Invoke actual Lambda with test events

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [AWS Lambda Testing](https://docs.aws.amazon.com/lambda/latest/dg/lambda-testing.html)
- [Durable Functions SDK](https://docs.aws.amazon.com/lambda/latest/dg/durable-execution-sdk.html)
