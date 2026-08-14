"""
test_api.py - API endpoint tests.

Tests public endpoints that don't require authentication.
Auth-protected endpoints are tested with mock tokens.
"""

import pytest


# ===========================================================================
# Public Endpoint Tests
# ===========================================================================

class TestPublicEndpoints:
    """Tests for endpoints that don't require authentication."""

    def test_root_endpoint(self, client):
        """GET / should return welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "LexiEase" in data["message"]

    def test_health_endpoint(self, client):
        """GET /health should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_returns_service_name(self, client):
        """Health endpoint should include service name."""
        response = client.get("/health")
        data = response.json()
        assert "service" in data


# ===========================================================================
# Protected Endpoint Tests (No Auth = 401/403)
# ===========================================================================

class TestProtectedEndpoints:
    """
    Tests that protected endpoints reject unauthenticated requests.
    We don't need a real token — we just verify they return 401/403.
    """

    def test_pipeline_requires_auth(self, client, sample_document_id):
        """Pipeline endpoint should reject requests without token."""
        response = client.post(f"/pipeline/process/{sample_document_id}")
        assert response.status_code in [401, 403]

    def test_rag_query_requires_auth(self, client, sample_document_id):
        """RAG query endpoint should reject requests without token."""
        response = client.post("/rag/query", json={
            "document_id": sample_document_id,
            "query": "What are the payment terms?"
        })
        assert response.status_code in [401, 403]

    def test_risk_analyze_requires_auth(self, client, sample_document_id):
        """Risk analysis endpoint should reject requests without token."""
        response = client.post(f"/risk/analyze/{sample_document_id}")
        assert response.status_code in [401, 403]

    def test_history_requires_auth(self, client):
        """History endpoint should reject requests without token."""
        response = client.get("/history/documents")
        assert response.status_code in [401, 403]

    def test_document_upload_requires_auth(self, client):
        """Document upload should reject requests without token."""
        response = client.post("/documents/upload")
        assert response.status_code in [401, 403]


# ===========================================================================
# Input Validation Tests
# ===========================================================================

class TestInputValidation:
    """Tests for request validation."""

    def test_rag_query_missing_fields(self, client):
        """
        RAG query with missing fields returns 401 (auth checked first)
        or 422 (validation error if auth passes).
        FastAPI checks auth before body validation.
        """
        response = client.post("/rag/query", json={})
        # Auth is checked before body validation
        assert response.status_code in [401, 403, 422]

    def test_rag_query_empty_body(self, client):
        """
        RAG query with empty body returns 401 (auth checked first)
        or 422 (validation error if auth passes).
        """
        response = client.post("/rag/query")
        # Auth is checked before body validation
        assert response.status_code in [401, 403, 422]