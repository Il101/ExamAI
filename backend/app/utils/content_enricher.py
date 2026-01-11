"""
Content Enricher Service
Parses AI-generated content for media markers, extracts images from source PDF,
uploads them to storage, and replaces markers with markdown image links.

Supports multi-file scenarios by reading source_meta.json and using file_index.
"""
import re
import json
import logging
import io
import os
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
from datetime import datetime

from app.utils.media_extractor import MediaExtractor
from app.integrations.storage.supabase_storage import SupabaseStorage
from app.core.config import settings

logger = logging.getLogger(__name__)

class ContentEnricher:
    """
    Enriches content by replacing [[MEDIAREF]] or [[MEDIA_REF]] markers with actual image links.
    Supports multi-file uploads using file_index in markers.
    """
    
    def __init__(self, storage: SupabaseStorage):
        self.storage = storage
        self.extractor = MediaExtractor()
        # Regex to find [[MEDIAREF: {...}]] or [[MEDIA_REF: {...}]]
        # Makes the underscore optional with _?
        self.marker_pattern = re.compile(r'\[\[MEDIA_?REF:\s*({.*?})\]\]', re.DOTALL)
        
    async def enrich_content(
        self, 
        content: str, 
        exam_id: UUID, 
        topic_id: UUID,
        original_file_url: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process content, extract images, and replace markers.
        
        Supports multi-file scenarios by loading source_meta.json for the exam.
        Each marker can include file_index to specify which source file to use.
        
        Args:
            content: Raw content with markers
            exam_id: Exam UUID
            topic_id: Topic UUID
            original_file_url: Path to primary PDF in storage (fallback for file_index=0)
            
        Returns:
            Tuple[enriched_content, media_references_list]
        """
        # Find all markers first
        markers = []
        for match in self.marker_pattern.finditer(content):
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                markers.append({
                    "full_match": match.group(0),
                    "data": data,
                    "span": match.span()
                })
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in media marker: {match.group(0)}")
                continue
                
        if not markers:
            return content, []
        
        # Load source files metadata
        source_files = await self._load_source_meta(exam_id)
        
        # If no source_meta.json, fallback to original_file_url
        if not source_files and original_file_url:
            source_files = [{"storage_path": original_file_url, "file_index": 0}]
        
        if not source_files:
            logger.warning(f"No source files available for exam {exam_id}, skipping enrichment")
            return content, []
            
        enriched_content = content
        media_references = []
        
        # Cache for downloaded PDFs: file_index -> local_path
        downloaded_pdfs: Dict[int, str] = {}
        
        try:
            for i, marker in enumerate(markers):
                data = marker["data"]
                page = data.get("page")
                box_2d = data.get("box_2d")
                caption = data.get("caption", "Image")
                file_index = data.get("file_index", 0)  # Default to first file
                
                if not page or not box_2d:
                    logger.warning(f"Marker missing page or box_2d: {data}")
                    continue
                
                # Get the correct source file
                source_file = self._get_source_file(source_files, file_index)
                if not source_file or not source_file.get("storage_path"):
                    logger.warning(f"No source file found for file_index={file_index}")
                    enriched_content = enriched_content.replace(marker['full_match'], "", 1)
                    continue
                
                storage_path = source_file["storage_path"]
                
                # Download PDF if not already cached
                if file_index not in downloaded_pdfs:
                    local_path = await self._download_pdf(storage_path)
                    if local_path:
                        downloaded_pdfs[file_index] = local_path
                    else:
                        enriched_content = enriched_content.replace(marker['full_match'], "", 1)
                        continue
                
                local_pdf_path = downloaded_pdfs[file_index]
                    
                # Extract image
                image = await self.extractor.extract_image_region(
                    local_pdf_path, 
                    page, 
                    box_2d
                )
                
                if image:
                    # Convert to bytes (WebP)
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='WEBP', quality=85)
                    img_bytes = img_byte_arr.getvalue()
                    
                    # Upload to storage
                    file_name = f"{topic_id}_{i+1}.webp"
                    media_storage_path = f"exams/{exam_id}/media/{file_name}"
                    
                    public_url = await self.storage.upload_file(
                        img_bytes, 
                        media_storage_path, 
                        content_type="image/webp"
                    )
                    
                    markdown = f"![{caption}]({public_url})"
                    enriched_content = enriched_content.replace(marker['full_match'], markdown, 1)
                    
                    media_references.append({
                        "url": public_url,
                        "caption": caption,
                        "source_page": page,
                        "source_file_index": file_index,
                        "box_2d": box_2d,
                        "original_marker": marker['data']
                    })
                else:
                    logger.warning(f"Failed to extract image for marker: {data}")
                    enriched_content = enriched_content.replace(marker['full_match'], "", 1)
                    
        finally:
            # Cleanup all downloaded PDFs
            for local_path in downloaded_pdfs.values():
                if os.path.exists(local_path):
                    try:
                        os.unlink(local_path)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temp PDF {local_path}: {e}")
                
        return enriched_content, media_references

    async def _load_source_meta(self, exam_id: UUID) -> List[Dict[str, Any]]:
        """Load source_meta.json for the exam to get list of source files."""
        try:
            meta_path = f"exams/{exam_id}/source_meta.json"
            meta_bytes = await self.storage.download_file(meta_path)
            meta_data = json.loads(meta_bytes.decode('utf-8'))
            
            # Add file_index to each entry for easier lookup
            for idx, item in enumerate(meta_data):
                item["file_index"] = idx
                
            logger.info(f"Loaded source_meta.json for exam {exam_id}: {len(meta_data)} files")
            return meta_data
        except Exception as e:
            logger.debug(f"Could not load source_meta.json for exam {exam_id}: {e}")
            return []
    
    def _get_source_file(self, source_files: List[Dict], file_index: int) -> Optional[Dict]:
        """Get source file by index."""
        for sf in source_files:
            if sf.get("file_index") == file_index:
                return sf
        # Fallback to first file if index not found
        if source_files and file_index == 0:
            return source_files[0]
        return None

    async def _download_pdf(self, file_path: str) -> Optional[str]:
        """Downloads PDF from storage to temp file"""
        try:
            file_bytes = await self.storage.download_file(file_path)
            
            # Create temp file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file_bytes)
                return tmp.name
        except Exception as e:
            logger.error(f"Failed to download PDF {file_path}: {e}")
            return None
