"""
Risk Analysis Service - M8-1
Analyzes legal document chunks and identifies risky clauses.

Uses Gemini to:
1. Read all document chunks
2. Identify potentially risky clauses
3. Categorize each risk as HIGH/MEDIUM/LOW
4. Explain why each clause is risky in plain language

Results are stored in the analyses table (risk_flags column as JSONB).
"""

import json
import logging
from google import genai
from app.services.vector_search_service import supabase as db
from app.config import GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
client = genai.Client(api_key=GEMINI_API_KEY)
GENERATION_MODEL = "models/gemini-3.5-flash"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def analyze_document_risks(document_id: str) -> dict:
    """
    Analyze all chunks of a document for risky legal clauses.

    Args:
        document_id: UUID of the document to analyze.

    Returns:
        Dict containing:
            - risk_flags: list of identified risks with level and explanation
            - total_risks: total number of risks found
            - high_count: number of HIGH risk items
            - medium_count: number of MEDIUM risk items
            - low_count: number of LOW risk items
            - analysis_id: UUID of saved analysis record

    Raises:
        Exception: If chunk retrieval, Gemini call, or DB save fails.
    """
    # ------------------------------------------------------------------
    # Step 1: Fetch all chunks for this document
    # ------------------------------------------------------------------
    logger.info(f"Fetching chunks for document {document_id}")

    response = (
        supabase.table("document_chunks")
        .select("chunk_text, chunk_index")
        .eq("document_id", document_id)
        .order("chunk_index")
        .execute()
    )

    chunks = response.data
    if not chunks:
        raise Exception("No chunks found for this document. Run the pipeline first.")

    # Combine all chunks into full document text for analysis
    full_text = "\n\n".join([c["chunk_text"] for c in chunks])

    # ------------------------------------------------------------------
    # Step 2: Build risk analysis prompt
    # ------------------------------------------------------------------
    prompt = f"""You are a legal risk analyzer. Analyze the following legal document and identify clauses that could be risky or unfavorable for the signing party.

LEGAL DOCUMENT:
{full_text}

INSTRUCTIONS:
- Identify ALL potentially risky clauses
- For each risk, provide:
  1. risk_level: "HIGH", "MEDIUM", or "LOW"
  2. clause: the exact or paraphrased risky text (keep it short)
  3. explanation: plain English explanation of why this is risky
  4. recommendation: what the user should do about it

- HIGH risk = could cause serious financial/legal harm
- MEDIUM risk = worth negotiating or being cautious about
- LOW risk = standard clause but user should be aware

IMPORTANT: Respond ONLY with a valid JSON array. No extra text before or after.

Example format:
[
  {{
    "risk_level": "HIGH",
    "clause": "Client shall not be liable for any indirect damages",
    "explanation": "This means if the company causes you losses, they won't pay for most of them.",
    "recommendation": "Try to negotiate removal or add a liability cap that protects both parties."
  }}
]

YOUR RESPONSE (JSON only):"""

    # ------------------------------------------------------------------
    # Step 3: Call Gemini for risk analysis
    # ------------------------------------------------------------------
    logger.info(f"Calling Gemini for risk analysis on document {document_id}")

    gemini_response = client.models.generate_content(
    model=GENERATION_MODEL,
    contents=prompt,
    config=genai.types.GenerateContentConfig(
        temperature=0.0,        # 0 = deterministic, same output every time
        top_p=1.0,              # Consider all tokens
        max_output_tokens=8192, # Enough for full analysis
    ),
)

    raw_text = gemini_response.text.strip()

    # ------------------------------------------------------------------
    # Step 4: Parse JSON response from Gemini
    # ------------------------------------------------------------------
    try:
        # Remove markdown code blocks if Gemini adds them
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        risk_flags = json.loads(raw_text)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {raw_text}")
        raise Exception(f"Failed to parse risk analysis response: {str(e)}")

    # ------------------------------------------------------------------
    # Step 5: Count risks by level
    # ------------------------------------------------------------------
    high_count = sum(1 for r in risk_flags if r.get("risk_level") == "HIGH")
    medium_count = sum(1 for r in risk_flags if r.get("risk_level") == "MEDIUM")
    low_count = sum(1 for r in risk_flags if r.get("risk_level") == "LOW")

    # ------------------------------------------------------------------
    # Step 6: Save to analyses table
    # ------------------------------------------------------------------
    logger.info(f"Saving risk analysis to DB for document {document_id}")

    save_response = (
        supabase.table("analyses")
        .insert({
            "document_id": document_id,
            "risk_flags": risk_flags,      # stored as JSONB
            "simplified_text": None,        # filled by RAG service separately
        })
        .execute()
    )

    analysis_id = save_response.data[0]["id"]

    return {
        "analysis_id": analysis_id,
        "risk_flags": risk_flags,
        "total_risks": len(risk_flags),
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
    }