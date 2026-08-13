"""
Pipeline Orchestrator - M6-4
Connects chunking -> embedding -> database storage in one workflow.

This service is called after text extraction from a document.
It processes the full document text and stores all chunks with
their embeddings into the document_chunks table in Supabase.
"""

import logging
from app.services.chunking_service import split_text_into_chunks
from app.services.embedding_service import get_embedding, TASK_TYPE_DOCUMENT
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Logger setup - helps us trace pipeline progress in production logs
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supabase client using SERVICE ROLE KEY (bypasses RLS for backend writes)
# Never expose this key to the frontend
# ---------------------------------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def process_document(document_id: str, full_text: str) -> dict:
    """
    Full pipeline: text -> chunks -> embeddings -> saved to Supabase.

    Args:
        document_id: UUID of the document in the documents table.
        full_text:   The complete extracted text from the document.

    Returns:
        A dict with:
            - chunks_created: number of chunks saved
            - success: True/False

    Raises:
        Exception: If chunking, embedding, or DB insert fails.
    """
    logger.info(f"Starting pipeline for document_id: {document_id}")

    # ------------------------------------------------------------------
    # Step 1: Chunk the text using split_text_into_chunks
    # ------------------------------------------------------------------
    chunks = split_text_into_chunks(full_text)  # ✅ correct function name
    logger.info(f"Created {len(chunks)} chunks for document {document_id}")

    if not chunks:
        logger.warning(f"No chunks created for document {document_id}")
        return {"chunks_created": 0, "success": False}

    # ------------------------------------------------------------------
    # Step 2: Generate embeddings + build rows for DB insert
    # ------------------------------------------------------------------
    rows = []
    for index, chunk in enumerate(chunks):
        try:
            logger.info(f"Embedding chunk {index + 1}/{len(chunks)}...")

            # Get 768-dim embedding for this chunk
            embedding = get_embedding(chunk, task_type=TASK_TYPE_DOCUMENT)

            # Build the row matching document_chunks table schema
            rows.append({
                "document_id": document_id,
                "chunk_text":  chunk,
                "chunk_index": index,
                "embedding":   embedding,  # list of 768 floats
            })

        except Exception as e:
            logger.error(f"Failed to embed chunk {index}: {str(e)}")
            raise Exception(f"Embedding failed at chunk {index + 1}: {str(e)}")

    # ------------------------------------------------------------------
    # Step 3: Save all rows to Supabase document_chunks table
    # ------------------------------------------------------------------
    try:
        response = supabase.table("document_chunks").insert(rows).execute()
        logger.info(
            f"Saved {len(rows)} chunks to DB for document {document_id}"
        )
    except Exception as e:
        logger.error(f"DB insert failed for document {document_id}: {str(e)}")
        raise Exception(f"Database insert failed: {str(e)}")

    return {
        "chunks_created": len(rows),
        "success": True,
    }