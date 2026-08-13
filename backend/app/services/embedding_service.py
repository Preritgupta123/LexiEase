"""
Embedding Service - M6-3
Converts text chunks into 768-dimension vectors using Google Gemini.

Uses the NEW google-genai SDK (not google-generativeai) because:
- text-embedding-004 is only available on v1 API endpoint
- The old SDK (google-generativeai) hits v1beta which does NOT support this model
"""

from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY

# ---------------------------------------------------------------------------
# Initialize the NEW Gemini client (uses v1 API endpoint correctly)
# ---------------------------------------------------------------------------
client = genai.Client(api_key=GEMINI_API_KEY)

# Gemini's latest embedding model - 768 dimensions, free tier friendly.
# Must match the vector(768) column in our document_chunks table.
EMBEDDING_MODEL = "gemini-embedding-001"

# Task type tells Gemini HOW this embedding will be used.
# RETRIEVAL_DOCUMENT = we are embedding document chunks for storage.
# RETRIEVAL_QUERY    = we are embedding a user question for search.
TASK_TYPE_DOCUMENT = "RETRIEVAL_DOCUMENT"
TASK_TYPE_QUERY    = "RETRIEVAL_QUERY"


def get_embedding(text: str, task_type: str = TASK_TYPE_DOCUMENT) -> list[float]:
    """
    Generate a single embedding vector for a piece of text.

    Args:
        text:      The text to embed (a chunk or a query).
        task_type: How this embedding will be used — affects
                   the model's internal optimization.

    Returns:
        A list of 768 floats representing the text's meaning.
        768 dimensions matches our pgvector column exactly.

    Raises:
        Exception: If the Gemini API call fails (network, quota, etc.)
    """
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=768,  # ✅ Force 768 to match pgvector column
        ),
    )

    return response.embeddings[0].values


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple text chunks.

    Processes chunks one by one to stay within Gemini free tier
    rate limits (60 requests/minute). For production, this could
    be parallelised with rate limiting.

    Args:
        texts: List of text chunks to embed.

    Returns:
        List of embedding vectors, one per input text.
        Order is preserved — embeddings[i] corresponds to texts[i].

    Raises:
        Exception: If any Gemini API call fails.
    """
    embeddings = []

    for i, text in enumerate(texts):
        try:
            embedding = get_embedding(text, task_type=TASK_TYPE_DOCUMENT)
            embeddings.append(embedding)
        except Exception as e:
            # Log which chunk failed so we can debug easily
            raise Exception(
                f"Failed to embed chunk {i + 1}/{len(texts)}: {str(e)}"
            )

    return embeddings