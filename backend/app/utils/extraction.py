import io
import logging
from typing import Optional
import PyPDF2
from docx import Document

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_data: bytes) -> str:
    """Extract text from PDF bytes using PyPDF2"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
        text_content = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
        return "\n".join(text_content).strip()
    except Exception as e:
        logger.error(f"PyPDF2 extraction failed: {e}")
        # Retain original exception for caller handling
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def extract_text_from_docx(file_data: bytes) -> str:
    """Extract text from DOCX bytes using python-docx"""
    try:
        doc = Document(io.BytesIO(file_data))
        text_content = []
        for para in doc.paragraphs:
            if para.text:
                text_content.append(para.text)
        return "\n".join(text_content).strip()
    except Exception as e:
        logger.error(f"Docx extraction failed: {e}")
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")

def extract_text_generic(file_data: bytes, mime_type: str) -> Optional[str]:
    """
    Generic extractor router based on mime type.
    Returns None if type is not supported.
    """
    mime = mime_type.lower()
    
    if "pdf" in mime:
        return extract_text_from_pdf(file_data)
    elif "word" in mime or "docx" in mime or "officedocument" in mime:
        return extract_text_from_docx(file_data)
    elif "text/plain" in mime:
        return file_data.decode('utf-8', errors='ignore')
    
    logger.warning(f"Unsupported mime type for local extraction: {mime_type}")
    return None
