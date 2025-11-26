"""Supabase Storage integration for file management"""
from typing import Optional
from supabase import create_client, Client, ClientOptions
import logging

logger = logging.getLogger(__name__)

class SupabaseStorage:
    """Service for managing files in Supabase Storage"""
    
    def __init__(self, url: str, key: str, bucket: str = "exam-files"):
        # Service role key should not use session persistence or auto refresh
        self.client: Client = create_client(
            url, 
            key,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False,
            )
        )
        logger.info(f"SupabaseStorage initialized with URL: {url}, Key length: {len(key)}")
        if "service_role" not in key and len(key) < 100:
             logger.warning("Supabase key might not be a service_role key (usually long). Check .env!")
        self.bucket = bucket
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            buckets = self.client.storage.list_buckets()
            if not any(b.name == self.bucket for b in buckets):
                self.client.storage.create_bucket(self.bucket, options={"public": False})
                logger.info(f"Created bucket: {self.bucket}")
        except Exception as e:
            logger.warning(f"Bucket check failed: {e}")
    
    async def upload_file(self, file_content: bytes, file_path: str) -> str:
        """
        Upload file to storage
        
        Args:
            file_content: File bytes
            file_path: Path in bucket (e.g., "exams/uuid/file.txt")
        
        Returns:
            Public URL or signed URL
        """
        try:
            self.client.storage.from_(self.bucket).upload(
                file_path, 
                file_content,
                file_options={"content-type": "text/plain"}
            )
            logger.info(f"Uploaded file: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Upload failed for {file_path}: {e}")
            raise
    
    async def download_file(self, file_path: str) -> bytes:
        """
        Download file from storage
        
        Args:
            file_path: Path in bucket
        
        Returns:
            File content as bytes
        """
        try:
            response = self.client.storage.from_(self.bucket).download(file_path)
            logger.info(f"Downloaded file: {file_path}")
            return response
        except Exception as e:
            logger.error(f"Download failed for {file_path}: {e}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage
        
        Args:
            file_path: Path in bucket
        
        Returns:
            True if deleted successfully
        """
        try:
            self.client.storage.from_(self.bucket).remove([file_path])
            logger.info(f"Deleted file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Delete failed for {file_path}: {e}")
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in storage"""
        try:
            self.client.storage.from_(self.bucket).download(file_path)
            return True
        except:
            return False
