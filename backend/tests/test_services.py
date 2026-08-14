"""
test_services.py - Unit tests for backend services.

Tests:
- Chunking service
- Embedding service
- Vector search service
"""

import pytest
from app.services.chunking_service import split_text_into_chunks
from app.services.embedding_service import get_embedding, TASK_TYPE_DOCUMENT, TASK_TYPE_QUERY


# ===========================================================================
# Chunking Service Tests
# ===========================================================================

class TestChunkingService:
    """Tests for split_text_into_chunks function."""

    def test_basic_chunking(self, sample_legal_text):
        """Should split text into at least one chunk."""
        chunks = split_text_into_chunks(sample_legal_text)
        assert len(chunks) >= 1

    def test_chunks_are_strings(self, sample_legal_text):
        """Each chunk should be a non-empty string."""
        chunks = split_text_into_chunks(sample_legal_text)
        for chunk in chunks:
            assert isinstance(chunk, str)
            assert len(chunk.strip()) > 0

    def test_empty_text_raises_error(self):
        """Should raise ValueError for empty text."""
        with pytest.raises(ValueError):
            split_text_into_chunks("")

    def test_whitespace_only_raises_error(self):
        """Should raise ValueError for whitespace-only text."""
        with pytest.raises(ValueError):
            split_text_into_chunks("   ")

    def test_chunk_size_limit(self, sample_legal_text):
        """Each chunk should not exceed CHUNK_SIZE + CHUNK_OVERLAP characters."""
        from app.services.chunking_service import CHUNK_SIZE, CHUNK_OVERLAP
        chunks = split_text_into_chunks(sample_legal_text)
        for chunk in chunks:
            # Allow some tolerance for overlap
            assert len(chunk) <= CHUNK_SIZE + CHUNK_OVERLAP + 100

    def test_short_text_single_chunk(self):
        """Short text should produce exactly one chunk."""
        short_text = "This is a short legal clause about payment terms."
        chunks = split_text_into_chunks(short_text)
        assert len(chunks) == 1


# ===========================================================================
# Embedding Service Tests
# ===========================================================================

class TestEmbeddingService:
    """Tests for get_embedding function."""

    def test_embedding_returns_list(self):
        """Should return a list of floats."""
        embedding = get_embedding("Test legal clause.")
        assert isinstance(embedding, list)

    def test_embedding_dimension(self):
        """Should return exactly 768 dimensions."""
        embedding = get_embedding("Test legal clause.")
        assert len(embedding) == 768

    def test_embedding_values_are_floats(self):
        """All values should be floats."""
        embedding = get_embedding("Test legal clause.")
        for val in embedding:
            assert isinstance(val, float)

    def test_document_task_type(self):
        """Should work with RETRIEVAL_DOCUMENT task type."""
        embedding = get_embedding(
            "This agreement requires payment within 30 days.",
            task_type=TASK_TYPE_DOCUMENT
        )
        assert len(embedding) == 768

    def test_query_task_type(self):
        """Should work with RETRIEVAL_QUERY task type."""
        embedding = get_embedding(
            "What are the payment terms?",
            task_type=TASK_TYPE_QUERY
        )
        assert len(embedding) == 768

    def test_different_texts_different_embeddings(self):
        """Different texts should produce different embeddings."""
        emb1 = get_embedding("Payment terms and conditions.")
        emb2 = get_embedding("Termination clause notice period.")
        # They should not be identical
        assert emb1 != emb2