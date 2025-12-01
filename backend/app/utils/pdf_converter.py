"""
PDF Converter Utility
Handles conversion of various file formats to PDF using LibreOffice.
"""
import os
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def ensure_pdf(file_path: str, mime_type: str) -> str:
    """
    Ensures the file is in PDF format. Converts if necessary.
    
    Args:
        file_path: Path to the source file
        mime_type: MIME type of the source file
        
    Returns:
        Path to the PDF file (either original or converted)
        
    Raises:
        ValueError: If format is not supported
        RuntimeError: If conversion fails
    """
    if mime_type == "application/pdf":
        return file_path
    
    # DOCX
    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return convert_to_pdf(file_path)
    
    # PPTX
    if mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        return convert_to_pdf(file_path)
        
    # Legacy DOC
    if mime_type == "application/msword":
        return convert_to_pdf(file_path)
        
    # Legacy PPT
    if mime_type == "application/vnd.ms-powerpoint":
        return convert_to_pdf(file_path)
    
    # If we can't convert, but it might be text, we can't extract images from it easily
    # so we just return the path and let the caller handle it (or fail later)
    # But for this specific feature, we expect PDF for image extraction.
    
    raise ValueError(f"Unsupported format for PDF conversion: {mime_type}")

def convert_to_pdf(source_path: str) -> str:
    """
    Converts a document to PDF using LibreOffice headless mode.
    
    Args:
        source_path: Path to the source document
        
    Returns:
        Path to the generated PDF file
    """
    try:
        output_dir = os.path.dirname(source_path)
        
        # Run LibreOffice in headless mode
        # --convert-to pdf
        # --outdir <dir>
        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            source_path
        ]
        
        logger.info(f"Converting {source_path} to PDF...")
        result = subprocess.run(
            cmd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        
        # Calculate expected output path
        # LibreOffice replaces extension with .pdf
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
        
        if not os.path.exists(pdf_path):
            raise RuntimeError(f"PDF conversion failed: Output file not found at {pdf_path}")
            
        logger.info(f"Successfully converted to {pdf_path}")
        return pdf_path
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"LibreOffice conversion failed: {error_msg}")
        raise RuntimeError(f"Failed to convert file to PDF: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error during PDF conversion: {e}")
        raise
