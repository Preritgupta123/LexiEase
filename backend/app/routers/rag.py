"""
RAG Router - M7-4
API endpoint for legal document simplification using RAG.

Endpoint: POST /rag/query
- User sends a question + document_id
- We find relevant chunks via vector search
- We send chunks + question to Gemini
- We return a simplified answer
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.rag_service import simplify_document_query
from app.dependencies.auth import get_current_user
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Router setup
# ---------------------------------------------------------------------------
router = APIRouter(
    prefix="/rag",
    tags=["rag"],
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    """Request body for RAG query endpoint."""
    document_id: str
    query: str
    match_count: int = 5  # number of chunks to use as context


class ChunkSource(BaseModel):
    """A source chunk used in the RAG response."""
    chunk_text: str
    similarity: float
    chunk_index: int


class QueryResponse(BaseModel):
    """Response from RAG query endpoint."""
    answer: str
    query: str
    document_id: str
    source_chunks: list[ChunkSource]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/query", response_model=QueryResponse)
async def query_document(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Ask a question about a legal document and get a simplified answer.

    - Performs vector similarity search to find relevant chunks
    - Uses Gemini to generate a simplified explanation
    - Returns answer with source chunks for transparency

    Args:
        request: Contains document_id, query, and optional match_count.

    Returns:
        Simplified answer with source chunks used.

    Raises:
        404: If document not found or doesn't belong to user.
        500: If RAG pipeline fails.
    """
    # ------------------------------------------------------------------
    # Step 1: Verify document belongs to current user
    # ------------------------------------------------------------------
    try:
        response = (
            supabase.table("documents")
            .select("id, user_id, file_name")
            .eq("id", request.document_id)
            .single()
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Document not found: {str(e)}"
        )

    document = response.data

    # Security: ensure document belongs to current user
    if document["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to query this document."
        )

    # ------------------------------------------------------------------
    # Step 2: Validate query
    # ------------------------------------------------------------------
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty."
        )

    # ------------------------------------------------------------------
    # Step 3: Run RAG pipeline
    # ------------------------------------------------------------------
    try:
        result = simplify_document_query(
            query=request.query,
            document_id=request.document_id,
            match_count=request.match_count,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RAG pipeline failed: {str(e)}"
        )

    return QueryResponse(
        answer=result["answer"],
        query=result["query"],
        document_id=request.document_id,
        source_chunks=[
            ChunkSource(**chunk)
            for chunk in result["source_chunks"]
        ],
    )