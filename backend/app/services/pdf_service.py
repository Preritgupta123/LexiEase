"""
PDF text extraction service with OCR fallback.

Extraction strategy:
1. Try pypdf for digital PDFs (fast, free)
2. If no text found → use Gemini Vision OCR for scanned/image PDFs
3. Raises PDFExtractionError if both methods fail
"""

import io
import base64
import logging
from pypdf import PdfReader
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Initialize Gemini client for OCR
client = genai.Client(api_key=GEMINI_API_KEY)
VISION_MODEL = "models/gemini-3.5-flash"


class PDFExtractionError(Exception):
    """Raised when text cannot be extracted from a PDF."""
    pass


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all readable text from a PDF file's raw bytes.

    Strategy:
    1. Try pypdf for digital text extraction
    2. If no text found, fall back to Gemini Vision OCR

    Args:
        file_bytes: Raw binary content of the PDF file.

    Returns:
        Extracted text as a single string.

    Raises:
        PDFExtractionError: If the file is corrupted, password-protected,
                           or text cannot be extracted by any method.
    """
    # ------------------------------------------------------------------
    # Step 1: Try pypdf for digital PDFs
    # ------------------------------------------------------------------
    try:
        pdf_stream = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_stream)
    except Exception as e:
        raise PDFExtractionError(f"Could not read PDF file: {str(e)}")

    if reader.is_encrypted:
        raise PDFExtractionError(
            "This PDF is password-protected. Please upload an unprotected file."
        )

    extracted_pages = []
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                extracted_pages.append(page_text.strip())
        except Exception:
            continue

    full_text = "\n\n".join(extracted_pages)

    # ------------------------------------------------------------------
    # Step 2: If no text found, use Gemini Vision OCR
    # ------------------------------------------------------------------
    if not full_text.strip():
        logger.info("No text found with pypdf — trying Gemini Vision OCR...")
        try:
            full_text = _extract_text_with_gemini_ocr(file_bytes)
        except Exception as e:
            raise PDFExtractionError(
                f"Could not extract text from this PDF. "
                f"It may be corrupted or an unsupported format. Error: {str(e)}"
            )

    if not full_text.strip():
        raise PDFExtractionError(
            "No readable text found in this PDF even after OCR. "
            "Please ensure the document contains readable content."
        )

    return full_text


def _extract_text_with_gemini_ocr(file_bytes: bytes) -> str:
    """
    Use Gemini Vision to extract text from a scanned/image PDF.

    Sends the PDF directly to Gemini as a document for OCR processing.

    Args:
        file_bytes: Raw binary content of the PDF file.

    Returns:
        Extracted text string from Gemini Vision.
    """
    logger.info("Using Gemini Vision OCR for scanned PDF...")

    # Convert PDF bytes to base64
    pdf_base64 = base64.standard_b64encode(file_bytes).decode("utf-8")

    # Send to Gemini with OCR prompt
    response = client.models.generate_content(
        model=VISION_MODEL,
        contents=[
            types.Part.from_bytes(
                data=file_bytes,
                mime_type="application/pdf",
            ),
            """Extract ALL text from this PDF document exactly as it appears.
            Include all paragraphs, headings, clauses, and sections.
            Preserve the structure and order of the content.
            Do not summarize — extract the complete text."""
        ],
    )

    extracted_text = response.text.strip()
    logger.info(f"Gemini OCR extracted {len(extracted_text)} characters")

    return extracted_text