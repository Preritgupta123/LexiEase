"""
Document-related API endpoints.

Handles file upload, storage, and database record creation
for user-uploaded legal documents.
"""

import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.database import supabase
from app.schemas import DocumentResponse
from app.services.pdf_service import extract_text_from_pdf, PDFExtractionError

# APIRouter groups related endpoints together. The prefix means
# every route here automatically starts with /documents
# (e.g., this file's "/upload" becomes "/documents/upload").
router = APIRouter(prefix="/documents", tags=["documents"])

# Restrict uploads to PDF only for our MVP - keeps text
# extraction logic simple and predictable in the next step.
ALLOWED_CONTENT_TYPES = {"application/pdf"}

# 10 MB limit - reasonable for legal documents while
# preventing abuse/excessive storage costs on free tier.
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a legal document (PDF only).

    Flow:
    1. Validate file type and size
    2. Upload raw file bytes to Supabase Storage
       (path: documents/{user_id}/{unique_filename})
    3. Insert a record into the 'documents' table
    4. Return the created document's metadata
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

    # Generate a unique filename to avoid collisions if two users
    # (or the same user) upload files with identical names.
    unique_id = uuid.uuid4().hex
    storage_path = f"{user_id}/{unique_id}_{file.filename}"

    # --- Upload to Supabase Storage ---
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

    # --- Create database record ---
    try:
        result = (
            supabase.table("documents")
            .insert(
                {
                    "user_id": user_id,
                    "file_name": file.filename,
                    "file_path": storage_path,
                    "status": "uploaded",
                }
            )
            .execute()
        )
    except Exception as e:
        # If DB insert fails, clean up the orphaned file from storage
        # to avoid wasting storage space on untracked files.
        supabase.storage.from_("documents").remove([storage_path])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document record: {str(e)}",
        )

    created_document = result.data[0]
    return created_document

"""
Document-related API endpoints.
...
"""

import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.database import supabase
from app.schemas import DocumentResponse
from app.services.pdf_service import extract_text_from_pdf, PDFExtractionError  # ← NEW IMPORT

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    # ... your existing upload code stays exactly as is ...
    return created_document


# ↓↓↓ NEW FUNCTION GOES HERE, at the bottom ↓↓↓
@router.post("/extract-test")
async def extract_text_test(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    TEMPORARY endpoint to test PDF text extraction in isolation.
    """
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