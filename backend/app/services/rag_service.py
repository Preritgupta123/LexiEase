"""
RAG Service - M7-3
Retrieval Augmented Generation for legal document simplification.

Flow:
1. Search for relevant chunks using vector similarity
2. Build a context-aware prompt with those chunks
3. Send to Gemini for simplified explanation
4. Return structured response
"""

from google import genai
from app.services.vector_search_service import search_similar_chunks
from app.config import GEMINI_API_KEY

# ---------------------------------------------------------------------------
# Initialize Gemini client
# ---------------------------------------------------------------------------
client = genai.Client(api_key=GEMINI_API_KEY)

# Gemini model for text generation (free tier)
GENERATION_MODEL = "models/gemini-3.5-flash"


def simplify_document_query(
    query: str,
    document_id: str,
    match_count: int = 5,
) -> dict:
    """
    Answer a user query about a legal document using RAG.

    Args:
        query:       The user's question about the document.
        document_id: UUID of the document to query against.
        match_count: Number of chunks to use as context.

    Returns:
        Dict containing:
            - answer: Simplified explanation from Gemini
            - source_chunks: The chunks used as context
            - query: The original query

    Raises:
        Exception: If vector search or Gemini call fails.
    """
    # ------------------------------------------------------------------
    # Step 1: Retrieve relevant chunks
    # ------------------------------------------------------------------
    relevant_chunks = search_similar_chunks(
        query=query,
        document_id=document_id,
        match_count=match_count,
    )

    if not relevant_chunks:
        return {
            "answer": "I could not find relevant information in this document to answer your question.",
            "source_chunks": [],
            "query": query,
        }

    # ------------------------------------------------------------------
    # Step 2: Build context from retrieved chunks
    # ------------------------------------------------------------------
    context_parts = []
    for i, chunk in enumerate(relevant_chunks):
        context_parts.append(f"[Section {i+1}]\n{chunk['chunk_text']}")

    context = "\n\n".join(context_parts)

    # ------------------------------------------------------------------
    # Step 3: Build the RAG prompt
    # We tell Gemini exactly what role to play and what to do
    # ------------------------------------------------------------------
    prompt = f"""You are LexiEase, an AI assistant that helps people understand legal documents in simple, plain language.

A user has a question about a legal document. Use ONLY the provided document sections to answer.
If the answer is not in the provided sections, say so clearly.

DOCUMENT SECTIONS:
{context}

USER QUESTION:
{query}

INSTRUCTIONS:
- Answer in simple, clear language that anyone can understand
- Avoid legal jargon — if you must use a legal term, explain it
- Be concise but complete
- If there are important implications or risks, highlight them
- Format your response with clear paragraphs

YOUR ANSWER:"""

    # ------------------------------------------------------------------
    # Step 4: Call Gemini for generation
    # ------------------------------------------------------------------
    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
    )

    answer = response.text.strip()

    return {
        "answer": answer,
        "source_chunks": [
            {
                "chunk_text": chunk["chunk_text"],
                "similarity": chunk["similarity"],
                "chunk_index": chunk["chunk_index"],
            }
            for chunk in relevant_chunks
        ],
        "query": query,
    }