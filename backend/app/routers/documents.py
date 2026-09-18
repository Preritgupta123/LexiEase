"""
Document-related API endpoints.
Handles file upload, storage, text extraction, and database record creation.
"""

import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.database import supabase
from app.schemas import DocumentResponse
from app.services.pdf_service import extract_text_from_pdf, PDFExtractionError

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


# ---------------------------------------------------------------------------
# Helper: Validate PDF by magic bytes
# ✅ Don't trust file extension or content-type header alone
# ---------------------------------------------------------------------------
def validate_pdf_content(file_bytes: bytes) -> bool:
    """
    Validate file is actually a PDF by checking magic bytes.
    PDF files always start with %PDF (hex: 25 50 44 46)
    """
    return file_bytes[:4] == b'%PDF'


# ---------------------------------------------------------------------------
# Upload Endpoint
# ---------------------------------------------------------------------------
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a legal document (PDF only).

    Flow:
    1. Validate file type (content-type header)
    2. Read file bytes
    3. Validate file size
    4. Validate actual PDF content (magic bytes) ✅ Security
    5. Extract text from PDF
    6. Upload raw file bytes to Supabase Storage
    7. Insert record into documents table WITH extracted text
    8. Return the created document metadata
    """

    # ------------------------------------------------------------------
    # Step 1: Validate content-type header
    # ------------------------------------------------------------------
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported at this time.",
        )

    # ------------------------------------------------------------------
    # Step 2: Read file bytes ONCE
    # ✅ Only read once - second read returns empty bytes!
    # ------------------------------------------------------------------
    file_bytes = await file.read()

    # ------------------------------------------------------------------
    # Step 3: Validate file size
    # ------------------------------------------------------------------
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 10MB limit.",
        )

    # ------------------------------------------------------------------
    # Step 4: Validate actual PDF content using magic bytes
    # ✅ Prevents malicious files with .pdf extension
    # ------------------------------------------------------------------
    if not validate_pdf_content(file_bytes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content is not a valid PDF.",
        )

    user_id = current_user["user_id"]

    # ------------------------------------------------------------------
    # Step 5: Extract text from PDF
    # ------------------------------------------------------------------
    try:
        extracted_text = extract_text_from_pdf(file_bytes)
        doc_status = "extracted"
        logger.info(
            f"Text extracted successfully for user {user_id}: "
            f"{len(extracted_text)} characters"
        )
    except PDFExtractionError as e:
        # If extraction fails, still upload but mark as uploaded
        logger.warning(f"PDF extraction failed for user {user_id}: {str(e)}")
        extracted_text = None
        doc_status = "uploaded"

    # ------------------------------------------------------------------
    # Step 6: Upload to Supabase Storage
    # ------------------------------------------------------------------
    unique_id = uuid.uuid4().hex
    storage_path = f"{user_id}/{unique_id}_{file.filename}"

    try:
        supabase.storage.from_("documents").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type},
        )
        logger.info(f"File uploaded to storage: {storage_path}")
    except Exception as e:
        logger.error(f"Storage upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage.",
        )

    # ------------------------------------------------------------------
    # Step 7: Create database record WITH extracted text
    # ------------------------------------------------------------------
    try:
        result = (
            supabase.table("documents")
            .insert(
                {
                    "user_id": user_id,
                    "file_name": file.filename,
                    "file_path": storage_path,
                    "status": doc_status,
                    "extracted_text": extracted_text,
                }
            )
            .execute()
        )
    except Exception as e:
        # Cleanup: remove uploaded file if DB insert fails
        logger.error(f"Database insert failed: {str(e)}")
        supabase.storage.from_("documents").remove([storage_path])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document record.",
        )

    created_document = result.data[0]
    return created_document


# ---------------------------------------------------------------------------
# Extract Test Endpoint
# ---------------------------------------------------------------------------
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

    # Validate PDF content
    if not validate_pdf_content(file_bytes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content is not a valid PDF.",
        )

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


# ---------------------------------------------------------------------------
# Delete Endpoint
# ---------------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Step 1: Verify ownership
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Step 2: Delete chunks
    # ------------------------------------------------------------------
    try:
        supabase.table("document_chunks")\
            .delete()\
            .eq("document_id", document_id)\
            .execute()
    except Exception as e:
        logger.error(f"Failed to delete chunks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete document chunks."
        )

    # ------------------------------------------------------------------
    # Step 3: Delete analyses
    # ------------------------------------------------------------------
    try:
        supabase.table("analyses")\
            .delete()\
            .eq("document_id", document_id)\
            .execute()
    except Exception as e:
        logger.error(f"Failed to delete analyses: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete analyses."
        )

    # ------------------------------------------------------------------
    # Step 4: Delete from Supabase Storage
    # ------------------------------------------------------------------
    try:
        supabase.storage.from_("documents")\
            .remove([document["file_path"]])
    except Exception:
        # Continue even if storage delete fails
        logger.warning(f"Storage delete failed for {document['file_path']}")

    # ------------------------------------------------------------------
    # Step 5: Delete document record
    # ------------------------------------------------------------------
    try:
        supabase.table("documents")\
            .delete()\
            .eq("id", document_id)\
            .execute()
    except Exception as e:
        logger.error(f"Failed to delete document record: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete document record."
        )

    logger.info(f"Document {document_id} deleted by user {user_id}")

    return {
        "success": True,
        "message": f"Document {document_id} deleted successfully."
    }