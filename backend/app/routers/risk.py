"""
Risk Analysis Router - risk.py
Handles risk analysis endpoints for legal documents.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.risk_service import analyze_document_risks
from app.dependencies.auth import get_current_user
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/risk",
    tags=["risk"],
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------
class RiskFlag(BaseModel):
    """A single identified risk in the document."""
    risk_level: str          # HIGH, MEDIUM, or LOW
    clause: str              # the risky clause text
    explanation: str         # plain English explanation
    recommendation: str      # what to do about it


class RiskAnalysisResponse(BaseModel):
    """Full risk analysis response."""
    analysis_id: str
    document_id: str
    file_name: str
    total_risks: int
    high_count: int
    medium_count: int
    low_count: int
    risk_flags: list[RiskFlag]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/analyze/{document_id}", response_model=RiskAnalysisResponse)
async def analyze_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze a document for risk clauses.

    Flow:
      1. Verify document exists and belongs to user
      2. Check if analysis already exists → return cached
      3. If no cache → run Gemini analysis with temperature=0
      4. Save and return results
    """

    # ------------------------------------------------------------------
    # Step 1: Verify document exists and belongs to current user
    # ------------------------------------------------------------------
    try:
        response = (
            supabase.table("documents")
            .select("id, user_id, file_name")
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

    # Security check
    if document["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to analyze this document."
        )

    # ------------------------------------------------------------------
    # Step 1.5: Return cached analysis if it exists
    # ------------------------------------------------------------------
    try:
        existing = (
            supabase.table("analyses")
            .select("id, risk_flags, created_at")
            .eq("document_id", document_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if existing.data:
            cached = existing.data[0]
            risk_flags = cached["risk_flags"]

            logger.info(
                f"Returning cached analysis {cached['id']} "
                f"for document {document_id}"
            )

            return RiskAnalysisResponse(
                analysis_id=cached["id"],
                document_id=document_id,
                file_name=document["file_name"],
                total_risks=len(risk_flags),
                high_count=sum(
                    1 for r in risk_flags if r.get("risk_level") == "HIGH"
                ),
                medium_count=sum(
                    1 for r in risk_flags if r.get("risk_level") == "MEDIUM"
                ),
                low_count=sum(
                    1 for r in risk_flags if r.get("risk_level") == "LOW"
                ),
                risk_flags=[RiskFlag(**flag) for flag in risk_flags],
            )

    except Exception as e:
        logger.warning(
            f"Cache check failed, generating fresh analysis: {str(e)}"
        )

    # ------------------------------------------------------------------
    # Step 2: Run fresh risk analysis (only if no cache exists)
    # ------------------------------------------------------------------
    try:
        result = analyze_document_risks(document_id)
    except Exception as e:
        if "No chunks found" in str(e):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Document has no chunks. Please run the pipeline first: "
                    f"POST /pipeline/process/{document_id}"
                )
            )
        raise HTTPException(
            status_code=500,
            detail=f"Risk analysis failed: {str(e)}"
        )

    return RiskAnalysisResponse(
        analysis_id=result["analysis_id"],
        document_id=document_id,
        file_name=document["file_name"],
        total_risks=result["total_risks"],
        high_count=result["high_count"],
        medium_count=result["medium_count"],
        low_count=result["low_count"],
        risk_flags=[RiskFlag(**flag) for flag in result["risk_flags"]],
    )


# ---------------------------------------------------------------------------
@router.get("/analyses/{document_id}")
async def get_document_analyses(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get all previous analyses for a document."""

    # Verify document ownership
    try:
        doc_response = (
            supabase.table("documents")
            .select("id, user_id, file_name")
            .eq("id", document_id)
            .single()
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc_response.data["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Permission denied.")

    # Fetch all analyses for this document
    analyses_response = (
        supabase.table("analyses")
        .select("id, risk_flags, simplified_text, created_at")
        .eq("document_id", document_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "document_id": document_id,
        "file_name": doc_response.data["file_name"],
        "analyses": analyses_response.data,
    }