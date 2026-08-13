"""
Risk Analysis Router - M8-2
API endpoint to trigger risk analysis for a legal document.

Endpoint: POST /risk/analyze/{document_id}
- Fetches all document chunks
- Sends to Gemini for risk identification
- Saves results to analyses table
- Returns structured risk report
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.risk_service import analyze_document_risks
from app.dependencies.auth import get_current_user
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Router setup
# ---------------------------------------------------------------------------
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
    Analyze a legal document for risky clauses.

    - Reads all document chunks from the database
    - Uses Gemini to identify HIGH/MEDIUM/LOW risk clauses
    - Saves analysis to the analyses table
    - Returns structured risk report

    Args:
        document_id: UUID of the document to analyze.

    Returns:
        Risk analysis report with categorized risk flags.

    Raises:
        404: If document not found or doesn't belong to user.
        400: If document has no chunks (pipeline not run yet).
        500: If analysis fails.
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
    # Step 2: Run risk analysis
    # ------------------------------------------------------------------
    try:
        result = analyze_document_risks(document_id)
    except Exception as e:
        if "No chunks found" in str(e):
            raise HTTPException(
                status_code=400,
                detail="Document has no chunks. Please run the pipeline first: POST /pipeline/process/{document_id}"
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


@router.get("/analyses/{document_id}")
async def get_document_analyses(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get all previous risk analyses for a document.

    Args:
        document_id: UUID of the document.

    Returns:
        List of previous analyses with risk flags.
    """
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