"""
Media Extractor Utility
Extracts image regions from PDF files based on coordinates.
"""
import fitz  # PyMuPDF
from PIL import Image
from typing import List, Optional
import io
import logging
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

class MediaExtractor:
    """Extracts images from PDF pages using coordinates"""
    
    def __init__(self):
        pass
    
    async def extract_image_region(
        self, 
        pdf_path: str, 
        page_num: int, 
        box_2d: List[int],
        padding_percent: float = 0.05,
        dpi: int = 150
    ) -> Optional[Image.Image]:
        """
        Extracts a region from a PDF page as a raster image (Asynchronous).
        """
        return await run_in_threadpool(
            self._extract_image_region_sync,
            pdf_path,
            page_num,
            box_2d,
            padding_percent,
            dpi
        )

    def _extract_image_region_sync(
        self, 
        pdf_path: str, 
        page_num: int, 
        box_2d: List[int],
        padding_percent: float = 0.05,
        dpi: int = 150
    ) -> Optional[Image.Image]:
        """
        Extracts a region from a PDF page as a raster image.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (1-based)
            box_2d: Coordinates [ymin, xmin, ymax, xmax] in 0-1000 scale
            padding_percent: Padding to add around the box (default 5%)
            dpi: Resolution for rasterization (default 150)
        
        Returns:
            PIL.Image object or None if extraction fails
        """
        doc = None
        try:
            doc = fitz.open(pdf_path)
            
            # Validate page number
            if page_num < 1 or page_num > len(doc):
                logger.error(f"Invalid page number {page_num} for PDF with {len(doc)} pages")
                return None
                
            page = doc[page_num - 1]  # 0-based index
            
            # Convert 0-1000 coordinates to PDF points
            page_rect = page.rect
            ymin, xmin, ymax, xmax = box_2d
            
            # Basic validation of coordinates
            if not (0 <= ymin < ymax <= 1000 and 0 <= xmin < xmax <= 1000):
                logger.error(f"Invalid box coordinates: {box_2d}")
                return None
            
            rect = fitz.Rect(
                xmin / 1000 * page_rect.width,
                ymin / 1000 * page_rect.height,
                xmax / 1000 * page_rect.width,
                ymax / 1000 * page_rect.height
            )
            
            # Add padding
            width = rect.width
            height = rect.height
            rect.x0 = max(0, rect.x0 - width * padding_percent)
            rect.y0 = max(0, rect.y0 - height * padding_percent)
            rect.x1 = min(page_rect.width, rect.x1 + width * padding_percent)
            rect.y1 = min(page_rect.height, rect.y1 + height * padding_percent)
            
            # Render region to pixmap
            pixmap = page.get_pixmap(clip=rect, dpi=dpi)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            
            return img
            
        except Exception as e:
            logger.error(f"Failed to extract image from {pdf_path} page {page_num}: {e}")
            return None
        finally:
            if doc:
                doc.close()
