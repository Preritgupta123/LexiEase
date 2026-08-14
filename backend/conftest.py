"""
conftest.py - Pytest configuration and shared fixtures.

Fixtures defined here are available to ALL test files automatically.
No need to import them — pytest discovers them automatically.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

# ---------------------------------------------------------------------------
# Test client fixture
# Creates a TestClient that simulates HTTP requests to our FastAPI app
# without actually starting a server.
# ---------------------------------------------------------------------------
@pytest.fixture
def client():
    """
    Returns a FastAPI TestClient for making test requests.
    Used in all API endpoint tests.
    """
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Sample test data fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_legal_text():
    """Sample legal text for testing chunking and embedding services."""
    return """
    This Agreement is entered into as of the date last signed below.
    The Contractor agrees to provide services as described in Schedule A.
    Payment shall be made within 30 days of invoice receipt.
    The Client shall not be liable for any indirect, incidental, or consequential damages.
    Either party may terminate this agreement with 30 days written notice.
    All disputes shall be resolved through binding arbitration.
    Confidentiality: Both parties agree to keep all proprietary information confidential
    for a period of 5 years following the termination of this agreement.
    """


@pytest.fixture
def sample_document_id():
    """Real document ID from our test database."""
    return "064c66df-193d-44bb-809b-78ba56c98e2f"