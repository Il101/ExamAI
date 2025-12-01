import asyncio
from datetime import datetime, timedelta, timezone
from dateutil import parser
import logging

from app.core.config import settings
from app.integrations.storage.supabase_storage import SupabaseStorage
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="cleanup_old_pdfs")
def cleanup_old_pdfs():
    """
    Delete original PDF files older than 48 hours.
    Scheduled to run periodically.
    """
    return asyncio.run(_cleanup_old_pdfs_async())

async def _cleanup_old_pdfs_async():
    """Async implementation of cleanup task"""
    logger.info("Starting cleanup of old PDFs")
    
    try:
        storage = SupabaseStorage(
            url=settings.SUPABASE_URL,
            key=settings.SUPABASE_KEY,
            bucket=settings.SUPABASE_BUCKET
        )
        
        # List files in original_files directory
        offset = 0
        limit = 100
        deleted_count = 0
        cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
        
        while True:
            files = await storage.list_files(path="original_files", limit=limit, offset=offset)
            if not files:
                break
                
            for file in files:
                try:
                    # Supabase returns dict with 'name', 'created_at', etc.
                    created_at_str = file.get("created_at")
                    if not created_at_str:
                        continue
                        
                    created_at = parser.isoparse(created_at_str)
                    
                    # Ensure timezone awareness
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    
                    if created_at < cutoff:
                        file_path = f"original_files/{file['name']}"
                        await storage.delete_file(file_path)
                        deleted_count += 1
                        logger.info(f"Deleted old PDF: {file_path}")
                        
                except Exception as e:
                    logger.error(f"Error processing file {file.get('name')}: {e}")
            
            if len(files) < limit:
                break
                
            offset += limit
            
        logger.info(f"Cleanup completed. Deleted {deleted_count} files.")
        return {"deleted_count": deleted_count}
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {"error": str(e)}
