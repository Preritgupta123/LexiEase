"""
Text Chunking Service.

Splits large legal document text into smaller, overlapping chunks
suitable for embedding and semantic search.

Why chunking?
- LLMs have token limits (can't process 50-page contracts at once)
- Smaller chunks = more precise retrieval
- Overlap ensures context is not lost at chunk boundaries
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter


# ---------------------------------------------------------------------------
# Constants — tuned for legal documents
# ---------------------------------------------------------------------------

# Each chunk is ~500 characters (~125 tokens) — small enough for precise
# retrieval, large enough to contain a complete legal clause.
CHUNK_SIZE = 500

# 50-character overlap between consecutive chunks so that a clause
# split across two chunks can still be retrieved fully.
CHUNK_OVERLAP = 50


def split_text_into_chunks(text: str) -> list[str]:
    """
    Split a large text string into smaller overlapping chunks.

    Args:
        text: The full extracted text from a legal document.

    Returns:
        A list of text chunk strings. Each chunk is at most
        CHUNK_SIZE characters with CHUNK_OVERLAP characters
        shared with its neighbours.

    Raises:
        ValueError: If the input text is empty or whitespace only.
    """
    if not text or not text.strip():
        raise ValueError("Cannot chunk empty text.")

    # RecursiveCharacterTextSplitter tries to split on:
    # 1. Double newlines (paragraphs)  ← best split point for legal docs
    # 2. Single newlines
    # 3. Spaces
    # 4. Individual characters (last resort)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,          # count characters (not tokens)
        separators=["\n\n", "\n", ". ", " ", ""],  # legal-doc friendly
    )

    chunks = splitter.split_text(text)

    # Filter out any empty/whitespace-only chunks that may result
    # from splitting documents with lots of blank lines.
    chunks = [c.strip() for c in chunks if c.strip()]

    return chunks