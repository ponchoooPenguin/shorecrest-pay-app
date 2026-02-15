"""
OCR Module - PDF to Text extraction using Tesseract
"""

import os
import tempfile
from pathlib import Path
from pdf2image import convert_from_path, convert_from_bytes
import pytesseract
from PIL import Image


def extract_text_from_pdf(pdf_path: str = None, pdf_bytes: bytes = None) -> str:
    """
    Extract text from a PDF using Tesseract OCR.
    
    Args:
        pdf_path: Path to PDF file (optional)
        pdf_bytes: PDF file bytes (optional, for Streamlit uploads)
    
    Returns:
        Extracted text as string
    """
    if pdf_path:
        images = convert_from_path(pdf_path, dpi=300)
    elif pdf_bytes:
        images = convert_from_bytes(pdf_bytes, dpi=300)
    else:
        raise ValueError("Must provide either pdf_path or pdf_bytes")
    
    # Extract text from all pages (usually just first page for AIA forms)
    all_text = []
    for i, image in enumerate(images):
        # Use Tesseract to extract text
        text = pytesseract.image_to_string(image, config='--psm 6')
        all_text.append(text)
        
        # For AIA G702 forms, we typically only need the first page
        if i == 0:
            break
    
    return "\n".join(all_text)


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image file using Tesseract OCR.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Extracted text as string
    """
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, config='--psm 6')
    return text


if __name__ == "__main__":
    # Test with sample PDF
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        text = extract_text_from_pdf(pdf_path=pdf_path)
        print(text)
    else:
        print("Usage: python ocr.py <path_to_pdf>")
