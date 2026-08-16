"""
PDF Service - Text extraction from PDF documents.

Strategy:
  1. Try pypdf first (fast, works for text-based PDFs)
  2. If no text found, use PyMuPDF to convert pages to images
     then send each page image to Gemini Vision for OCR
     (works for scanned/image-based PDFs, no poppler needed)
"""

import io
import logging
import pymupdf as fitz   # pymupdf - converts PDF pages to images without poppler

from pypdf import PdfReader
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY

# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gemini client - used for Vision OCR on image-based PDFs
# ---------------------------------------------------------------------------
client = genai.Client(api_key=GEMINI_API_KEY)
VISION_MODEL = "gemini-flash-latest"  # supports image input reliably


# ---------------------------------------------------------------------------
# Custom Exception
# ---------------------------------------------------------------------------
class PDFExtractionError(Exception):
    """Raised when text cannot be extracted from a PDF."""
    pass


# ---------------------------------------------------------------------------
# PUBLIC FUNCTION - called by documents.py router
# ---------------------------------------------------------------------------
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF file (bytes).

    Flow:
      Step 1 → Try pypdf (handles text-based PDFs instantly)
      Step 2 → If empty, use PyMuPDF + Gemini Vision OCR
               (handles scanned/image-based PDFs)

    Args:
        file_bytes: Raw bytes of the uploaded PDF file

    Returns:
        Extracted text as a string

    Raises:
        PDFExtractionError: If text cannot be extracted by any method
    """

    # ------------------------------------------------------------------
    # Step 1: Try pypdf for text-based PDFs
    # ------------------------------------------------------------------
    try:
        pdf_stream = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_stream)
    except Exception as e:
        raise PDFExtractionError(f"Could not read PDF file: {str(e)}")

    # Check for password protection
    if reader.is_encrypted:
        raise PDFExtractionError(
            "This PDF is password-protected. Please upload an unprotected file."
        )

    # Extract text page by page
    extracted_pages = []
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                extracted_pages.append(page_text.strip())
        except Exception:
            continue  # skip problematic pages, don't crash

    full_text = "\n\n".join(extracted_pages)

    # ------------------------------------------------------------------
    # Step 2: If pypdf found no text → use Gemini Vision OCR
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

    # Final check - if still empty after OCR
    if not full_text.strip():
        raise PDFExtractionError(
            "No readable text found in this PDF even after OCR. "
            "Please ensure the document contains readable content."
        )

    logger.info(f"Successfully extracted {len(full_text)} characters from PDF")
    return full_text


# ---------------------------------------------------------------------------
# PRIVATE FUNCTION - Gemini Vision OCR using PyMuPDF page-by-page
# ---------------------------------------------------------------------------
def _extract_text_with_gemini_ocr(file_bytes: bytes) -> str:
    """
    Convert each PDF page to a PNG image using PyMuPDF,
    then send each image to Gemini Vision API for text extraction.

    Why page-by-page?
      - Gemini Vision works best with clear images
      - Avoids token/size limits of sending entire PDF
      - Each page processed independently = better accuracy

    Args:
        file_bytes: Raw bytes of the PDF file

    Returns:
        Combined extracted text from all pages
    """
    logger.info("Using PyMuPDF + Gemini Vision OCR for scanned PDF...")

    # Open PDF with PyMuPDF (fitz) - works without poppler
    try:
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise PDFExtractionError(f"PyMuPDF could not open PDF: {str(e)}")

    total_pages = len(pdf_document)
    logger.info(f"PDF has {total_pages} page(s) to process via OCR")

    all_pages_text = []

    for page_num in range(total_pages):
        try:
            # --- Convert PDF page to PNG image ---
            page = pdf_document[page_num]

            # Matrix(2, 2) = 2x zoom for better OCR resolution (144 DPI)
            # Higher = better quality but slower. 2x is the sweet spot.
            mat = fitz.Matrix(2, 2)
            pixmap = page.get_pixmap(matrix=mat)
            # Convert pixmap to PNG bytes
            img_bytes = pixmap.tobytes("png")
            logger.info(
                f"Processing page {page_num + 1}/{total_pages} "
                f"({len(img_bytes)} bytes)"
            )
            # --- Send PNG image to Gemini Vision ---
            response = client.models.generate_content(
                model=VISION_MODEL,
                contents=[
                    types.Part.from_bytes(
                        data=img_bytes,
                        mime_type="image/png",  # ✅ Correct: image not PDF
                    ),
                    """Extract ALL text from this document image exactly as it appears.
Include all paragraphs, headings, clauses, numbers, dates, and sections.
Preserve the structure and order of the content.
Do not summarize — extract the complete text word for word.""",
                ],
            )
            page_text = response.text.strip()

            if page_text:
                all_pages_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                logger.info(
                    f"Page {page_num + 1}: extracted {len(page_text)} characters"
                )
            else:
                logger.warning(f"Page {page_num + 1}: Gemini returned empty text")

        except Exception as e:
            # Log but continue — don't fail entire document for one page
            logger.error(f"Error processing page {page_num + 1}: {str(e)}")
            continue
    # Close the PDF document to free memory
    pdf_document.close()

    combined_text = "\n\n".join(all_pages_text)
    logger.info(
        f"Gemini Vision OCR completed: {len(combined_text)} total characters "
        f"from {len(all_pages_text)}/{total_pages} pages"
    )

    return combined_text