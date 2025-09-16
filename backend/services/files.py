from models import TreeItem
import os
import uuid
import aiofiles
from typing import Dict, Any, Optional
from fastapi import UploadFile
from datetime import datetime


class FileService:
    UPLOAD_DIR = "uploads"
    
    @classmethod
    def _generate_upload_path(cls) -> str:
        """Generate the organized upload path: uploads/year/month/file-id-uuid/"""
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        
        # Create the folder structure: uploads/year/month/file-id-uuid
        folder_path = os.path.join(cls.UPLOAD_DIR, year, month, str(uuid.uuid4()))
        return folder_path
    
    @classmethod
    async def save_uploaded_file(cls, file: UploadFile) -> Dict[str, Any]:
        """Save uploaded file to disk and return file info"""

        upload_path = cls._generate_upload_path()
        os.makedirs(upload_path, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_path, unique_filename)
        
        # Save file
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return {
            "original_name": file.filename,
            "name": unique_filename,
            "file_path": file_path,
            "file_size": len(content),
            "mime_type": file.content_type or "application/octet-stream"
        }
    
    @classmethod
    async def get_file(cls, file_id: str) -> Optional[TreeItem]:
        """Get file by ID"""
        return await TreeItem.get_or_none(id=file_id, object_type__in=["raw_file", "geo_raster_file"])
    
    @classmethod
    async def delete_file(cls, file_id: str) -> bool:
        """Delete file and remove from disk"""
        file_obj = await TreeItem.get_or_none(id=file_id, object_type__in=["raw_file", "geo_raster_file"])
        if not file_obj:
            return False
            
        # Remove file from disk
        file_path = await file_obj.get_file_path()
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            
        await file_obj.delete()
        return True
