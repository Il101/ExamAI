"""
Content Enricher Service
Parses AI-generated content for media markers, extracts images from source PDF,
uploads them to storage, and replaces markers with markdown image links.
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
    Enriches content by replacing [[MEDIA_REF]] markers with actual image links.
    """
    
    def __init__(self, storage: SupabaseStorage):
        self.storage = storage
        self.extractor = MediaExtractor()
        # Regex to find [[MEDIA_REF: {...}]]
        # Non-greedy match for content inside [[...]]
        self.marker_pattern = re.compile(r'\[\[MEDIA_REF:\s*({.*?})\]\]', re.DOTALL)
        
    async def enrich_content(
        self, 
        content: str, 
        exam_id: UUID, 
        topic_id: UUID,
        original_file_url: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process content, extract images, and replace markers.
        
        Args:
            content: Raw content with markers
            exam_id: Exam UUID
            topic_id: Topic UUID
            original_file_url: Path to original PDF in storage
            
        Returns:
            Tuple[enriched_content, media_references_list]
        """
        if not original_file_url:
            logger.warning(f"No original file URL for exam {exam_id}, skipping enrichment")
            return content, []
            
        # Find all markers
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
            
        # Download original PDF
        local_pdf_path = await self._download_pdf(original_file_url)
        if not local_pdf_path:
            return content, []
            
        enriched_content = content
        media_references = []
        
        try:
            # Process markers in reverse order to maintain string indices
            # (though we are doing replace, so order matters less if matches are unique)
            # But replace() might replace identical markers, so we should be careful.
            # Better strategy: Reconstruct string or use unique replacements.
            # Since markers might be identical, let's process them one by one.
            
            # Actually, simpler approach: Iterate and replace.
            # But we need to handle the case where extraction fails.
            
            for i, marker in enumerate(markers):
                data = marker["data"]
                page = data.get("page")
                box_2d = data.get("box_2d")
                caption = data.get("caption", "Image")
                
                if not page or not box_2d:
                    continue
                    
                # Extract image
                image = self.extractor.extract_image_region(
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
                    storage_path = f"exams/{exam_id}/media/{file_name}"
                    
                    # Upload (content_type is supported now)
                    public_url = await self.storage.upload_file(
                        img_bytes, 
                        storage_path, 
                        content_type="image/webp"
                    )
                    
                    # Construct markdown
                    # We use the storage path relative to bucket or full URL?
                    # Frontend usually needs full URL or we have a proxy.
                    # SupabaseStorage returns the path.
                    # Let's assume we need to construct the full URL or use the path if frontend handles it.
                    # For now, let's use the path returned by upload_file.
                    
                    # Get public URL if possible, or just use the path
                    # If bucket is private, we might need signed URLs, but for now assuming public access or proxy
                    # Let's use the path and let frontend resolve it
                    
                    # Actually, let's try to get a full URL if we can, but SupabaseStorage.upload_file returns file_path.
                    # Let's stick to file_path for now.
                    
                    markdown = f"![{caption}]({public_url})"
                    
                    # Replace marker in content
                    # We use replace(marker['full_match'], markdown, 1) to replace only the first occurrence
                    # But if there are duplicates, we might replace the wrong one if we are not careful.
                    # However, since we iterate in order, and if we replace from the start...
                    # Wait, if we have duplicates, replace(..., 1) will always replace the first one.
                    # So we should iterate and replace.
                    
                    enriched_content = enriched_content.replace(marker['full_match'], markdown, 1)
                    
                    media_references.append({
                        "url": public_url,
                        "caption": caption,
                        "source_page": page,
                        "box_2d": box_2d,
                        "original_marker": marker['data']
                    })
                else:
                    logger.warning(f"Failed to extract image for marker: {data}")
                    # Remove marker or leave it? Better to remove it to clean up.
                    enriched_content = enriched_content.replace(marker['full_match'], "", 1)
                    
        finally:
            # Cleanup local PDF
            if os.path.exists(local_pdf_path):
                os.unlink(local_pdf_path)
                
        return enriched_content, media_references

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
