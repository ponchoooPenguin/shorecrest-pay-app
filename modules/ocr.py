"""
OCR Module - PDF to Text extraction using PyMuPDF
No system dependencies required (no poppler/tesseract)
"""

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str = None, pdf_bytes: bytes = None) -> str:
    """
    Extract text from a PDF using PyMuPDF.
    
    Args:
        pdf_path: Path to PDF file (optional)
        pdf_bytes: PDF file bytes (optional, for Streamlit uploads)
    
    Returns:
        Extracted text as string
    """
    if pdf_path:
        doc = fitz.open(pdf_path)
    elif pdf_bytes:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    else:
        raise ValueError("Must provide either pdf_path or pdf_bytes")
    
    # Extract text from first page (AIA G702 forms are usually single page)
    all_text = []
    for page_num in range(min(len(doc), 2)):  # First 2 pages max
        page = doc[page_num]
        text = page.get_text()
        all_text.append(text)
    
    doc.close()
    return "\n".join(all_text)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        text = extract_text_from_pdf(pdf_path=pdf_path)
        print(text)
    else:
        print("Usage: python ocr.py <path_to_pdf>")
