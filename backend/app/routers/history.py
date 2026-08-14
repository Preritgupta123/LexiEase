"""
History Router - M9
API endpoints for fetching user's document and analysis history.

Endpoints:
- GET /history/documents         — list all user's documents
- GET /history/documents/{id}    — get single document with analyses
"""

from fastapi import APIRouter, HTTPException, Depends
from app.dependencies.auth import get_current_user
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client

router = APIRouter(
    prefix="/history",
    tags=["history"],
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


@router.get("/documents")
async def get_user_documents(
    current_user: dict = Depends(get_current_user),
):
    """
    Get all documents uploaded by the current user.

    Returns:
        List of documents with basic info and analysis count.
    """
    user_id = current_user["user_id"]

    # Fetch all documents for this user
    response = (
        supabase.table("documents")
        .select("id, file_name, file_path, status, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    documents = response.data

    # For each document, count how many analyses exist
    result = []
    for doc in documents:
        analyses_response = (
            supabase.table("analyses")
            .select("id", count="exact")
            .eq("document_id", doc["id"])
            .execute()
        )
        doc["analyses_count"] = analyses_response.count or 0
        result.append(doc)

    return {
        "documents": result,
        "total": len(result),
    }


@router.get("/documents/{document_id}")
async def get_document_detail(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a single document with all its analyses.

    Args:
        document_id: UUID of the document.

    Returns:
        Document details with full analysis history.
    """
    user_id = current_user["user_id"]

    # Fetch document
    try:
        doc_response = (
            supabase.table("documents")
            .select("id, file_name, file_path, status, created_at, extracted_text")
            .eq("id", document_id)
            .eq("user_id", user_id)  # ensures ownership
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    document = doc_response.data

    # Fetch all analyses for this document
    analyses_response = (
        supabase.table("analyses")
        .select("id, risk_flags, simplified_text, created_at")
        .eq("document_id", document_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "document": document,
        "analyses": analyses_response.data,
        "analyses_count": len(analyses_response.data),
    }