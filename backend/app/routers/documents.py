"""
Document-related API endpoints.
Handles file upload, storage, text extraction, and database record creation.
"""

import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.database import supabase
from app.schemas import DocumentResponse
from app.services.pdf_service import extract_text_from_pdf, PDFExtractionError

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a legal document (PDF only).

    Flow:
    1. Validate file type and size
    2. Extract text from PDF ✅ NEW
    3. Upload raw file bytes to Supabase Storage
    4. Insert record into documents table WITH extracted text ✅ NEW
    5. Return the created document metadata
    """
    # --- Validation ---
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported at this time.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 10MB limit.",
        )

    user_id = current_user["user_id"]

    # --- Extract text from PDF FIRST ---
    try:
        extracted_text = extract_text_from_pdf(file_bytes)
        doc_status = "extracted"
    except PDFExtractionError:
        # If extraction fails, still upload but mark as uploaded
        extracted_text = None
        doc_status = "uploaded"

    # --- Upload to Supabase Storage ---
    unique_id = uuid.uuid4().hex
    storage_path = f"{user_id}/{unique_id}_{file.filename}"

    try:
        supabase.storage.from_("documents").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {str(e)}",
        )

    # --- Create database record WITH extracted text ---
    try:
        result = (
            supabase.table("documents")
            .insert(
                {
                    "user_id": user_id,
                    "file_name": file.filename,
                    "file_path": storage_path,
                    "status": doc_status,           # ✅ extracted or uploaded
                    "extracted_text": extracted_text, # ✅ text from PDF
                }
            )
            .execute()
        )
    except Exception as e:
        supabase.storage.from_("documents").remove([storage_path])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document record: {str(e)}",
        )

    created_document = result.data[0]
    return created_document


@router.post("/extract-test")
async def extract_text_test(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Test PDF text extraction in isolation."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    file_bytes = await file.read()

    try:
        extracted_text = extract_text_from_pdf(file_bytes)
    except PDFExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return {
        "character_count": len(extracted_text),
        "preview": extracted_text[:500],
    }

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a document and all its associated data.

    Flow:
    1. Verify document belongs to current user
    2. Delete all chunks from document_chunks table
    3. Delete all analyses from analyses table
    4. Delete file from Supabase Storage
    5. Delete document record from documents table
    """
    user_id = current_user["user_id"]

    # --- Verify ownership ---
    try:
        doc_response = (
            supabase.table("documents")
            .select("id, user_id, file_path")
            .eq("id", document_id)
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    document = doc_response.data

    if document["user_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this document."
        )

    # --- Delete chunks ---
    try:
        supabase.table("document_chunks")\
            .delete()\
            .eq("document_id", document_id)\
            .execute()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document chunks: {str(e)}"
        )

    # --- Delete analyses ---
    try:
        supabase.table("analyses")\
            .delete()\
            .eq("document_id", document_id)\
            .execute()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete analyses: {str(e)}"
        )

    # --- Delete from Supabase Storage ---
    try:
        supabase.storage.from_("documents")\
            .remove([document["file_path"]])
    except Exception:
        pass  # Continue even if storage delete fails

    # --- Delete document record ---
    try:
        supabase.table("documents")\
            .delete()\
            .eq("id", document_id)\
            .execute()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document record: {str(e)}"
        )

    return {
        "success": True,
        "message": f"Document {document_id} deleted successfully."
    }