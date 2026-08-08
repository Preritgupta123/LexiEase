"""
PDF text extraction service.

Pure business logic for extracting readable text from PDF files.
Kept separate from API/router code so this logic can be reused
or tested independently of HTTP concerns.
"""

import io
from pypdf import PdfReader


class PDFExtractionError(Exception):
    """Raised when text cannot be extracted from a PDF."""
    pass


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all readable text from a PDF file's raw bytes.

    Args:
        file_bytes: Raw binary content of the PDF file.

    Returns:
        Extracted text as a single string, with pages
        separated by double newlines for readability.

    Raises:
        PDFExtractionError: If the file is corrupted, password-protected,
                             or contains no extractable text (e.g., a
                             scanned image PDF with no OCR applied).
    """
    try:
        # io.BytesIO wraps our raw bytes so pypdf can read it
        # as if it were a file, without writing to disk first.
        pdf_stream = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_stream)
    except Exception as e:
        raise PDFExtractionError(f"Could not read PDF file: {str(e)}")

    if reader.is_encrypted:
        raise PDFExtractionError(
            "This PDF is password-protected. Please upload an "
            "unprotected file."
        )

    extracted_pages = []
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                extracted_pages.append(page_text.strip())
        except Exception:
            # If one page fails to extract, skip it rather than
            # failing the entire document - partial results are
            # more useful than none for a multi-page document.
            continue

    full_text = "\n\n".join(extracted_pages)

    if not full_text.strip():
        raise PDFExtractionError(
            "No readable text found in this PDF. It may be a "
            "scanned document or image-based file, which is not "
            "yet supported."
        )

    return full_text