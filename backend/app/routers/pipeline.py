"""
Pipeline Router - M6-5
API endpoint to trigger the chunking + embedding pipeline for a document.

Flow:
1. Frontend calls POST /pipeline/process/{document_id}
2. We fetch the extracted text from the documents table
3. We call process_document() to chunk + embed + store
4. We return the result
"""

from fastapi import APIRouter, HTTPException, Depends
from app.services.pipeline_service import process_document
from app.dependencies.auth import get_current_user
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Router setup - prefix means all routes start with /pipeline
# ---------------------------------------------------------------------------
router = APIRouter(
    prefix="/pipeline",
    tags=["pipeline"],  # groups endpoints in /docs UI
)

# Supabase client to fetch document text
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


@router.post("/process/{document_id}")
async def process_document_endpoint(
    document_id: str,
    current_user: dict = Depends(get_current_user),  # requires auth
):
    """
    Trigger the full pipeline for a document.

    - Fetches extracted text from the documents table
    - Chunks the text into smaller pieces
    - Generates 768-dim embeddings for each chunk
    - Saves all chunks + embeddings to document_chunks table

    Args:
        document_id: UUID of the document to process.

    Returns:
        JSON with chunks_created count and success status.

    Raises:
        404: If document not found or belongs to another user.
        400: If document has no extracted text.
        500: If pipeline fails.
    """
    # ------------------------------------------------------------------
    # Step 1: Fetch the document and verify ownership
    # ------------------------------------------------------------------
    try:
        response = (
            supabase.table("documents")
            .select("id, file_name, extracted_text, user_id")
            .eq("id", document_id)
            .single()
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Document not found: {str(e)}"
        )

    document = response.data

    # Security check: ensure document belongs to current user
    if document["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to process this document."
        )

    # ------------------------------------------------------------------
    # Step 2: Validate extracted text exists
    # ------------------------------------------------------------------
    extracted_text = document.get("extracted_text", "")
    if not extracted_text or not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Document has no extracted text. Please upload a valid document."
        )

    # ------------------------------------------------------------------
    # Step 3: Run the pipeline
    # ------------------------------------------------------------------
    try:
        result = process_document(document_id, extracted_text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline failed: {str(e)}"
        )

    return {
        "document_id": document_id,
        "file_name": document["file_name"],
        "chunks_created": result["chunks_created"],
        "success": result["success"],
        "message": f"Successfully processed document into {result['chunks_created']} chunks.",
    }