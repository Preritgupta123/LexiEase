"""
Vector Search Service - M7-1
Finds the most relevant document chunks for a given query
using pgvector cosine similarity search.

How it works:
1. Convert user query to a 768-dim embedding vector
2. Call match_document_chunks() SQL function via Supabase RPC
3. Return the most similar chunks ranked by similarity score
"""

from app.services.embedding_service import get_embedding, TASK_TYPE_QUERY
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Supabase client — uses service role to bypass RLS for vector search
# ---------------------------------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Number of chunks to retrieve for RAG context
# 5 chunks = enough context without hitting Gemini token limits
DEFAULT_MATCH_COUNT = 5


def search_similar_chunks(
    query: str,
    document_id: str,
    match_count: int = DEFAULT_MATCH_COUNT,
) -> list[dict]:
    """
    Find the most relevant chunks for a user query within a document.

    Args:
        query:       The user's question or search text.
        document_id: UUID of the document to search within.
        match_count: Number of top chunks to return (default 5).

    Returns:
        List of dicts, each containing:
            - id: chunk UUID
            - document_id: document UUID
            - chunk_text: the actual text content
            - chunk_index: position in document
            - similarity: float between 0-1 (1 = perfect match)

    Raises:
        Exception: If embedding or DB search fails.
    """
    # ------------------------------------------------------------------
    # Step 1: Convert query to embedding vector
    # Use TASK_TYPE_QUERY (not DOCUMENT) for search optimization
    # ------------------------------------------------------------------
    query_embedding = get_embedding(query, task_type=TASK_TYPE_QUERY)

    # ------------------------------------------------------------------
    # Step 2: Call the SQL function via Supabase RPC
    # RPC = Remote Procedure Call (calls our match_document_chunks function)
    # ------------------------------------------------------------------
    response = supabase.rpc(
        "match_document_chunks",
        {
            "query_embedding": query_embedding,
            "match_document_id": document_id,
            "match_count": match_count,
        },
    ).execute()

    # ------------------------------------------------------------------
    # Step 3: Return the matched chunks
    # ------------------------------------------------------------------
    return response.data or []