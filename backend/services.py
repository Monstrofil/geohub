from models import File, Tag, File_Pydantic, Tag_Pydantic
from tortoise.expressions import Q
import os
import uuid
import aiofiles
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException


class FileService:
    UPLOAD_DIR = "uploads"
    
    @classmethod
    async def ensure_upload_dir(cls):
        """Ensure upload directory exists"""
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)
    
    @classmethod
    async def save_uploaded_file(cls, file: UploadFile) -> Dict[str, Any]:
        """Save uploaded file to disk and return file info"""
        await cls.ensure_upload_dir()
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(cls.UPLOAD_DIR, unique_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return {
            "original_name": file.filename,
            "name": unique_filename,
            "file_path": file_path,
            "file_size": len(content),
            "mime_type": file.content_type or "application/octet-stream"
        }
    
    @classmethod
    async def create_file(cls, file_data: Dict[str, Any], tags: Dict[str, str] = None) -> File_Pydantic:
        """Create a new file record"""
        file_info = await cls.save_uploaded_file(file_data["file"])
        
        # Create file record
        file_obj = await File.create(
            name=file_info["name"],
            original_name=file_info["original_name"],
            file_path=file_info["file_path"],
            file_size=file_info["file_size"],
            mime_type=file_info["mime_type"],
            tags=tags or {}
        )
        
        return await File_Pydantic.from_tortoise_orm(file_obj)
    
    @classmethod
    async def get_file(cls, file_id: int) -> Optional[File_Pydantic]:
        """Get file by ID"""
        file_obj = await File.get_or_none(id=file_id)
        if file_obj:
            return await File_Pydantic.from_tortoise_orm(file_obj)
        return None
    
    @classmethod
    async def list_files(cls, skip: int = 0, limit: int = 100) -> List[File_Pydantic]:
        """List all files with pagination"""
        files = await File.all().offset(skip).limit(limit).order_by("-created_at")
        return [await File_Pydantic.from_tortoise_orm(file) for file in files]
    
    @classmethod
    async def update_file_tags(cls, file_id: int, tags: Dict[str, str]) -> Optional[File_Pydantic]:
        """Update file tags"""
        file_obj = await File.get_or_none(id=file_id)
        if not file_obj:
            return None
        
        file_obj.tags = tags
        await file_obj.save()
        return await File_Pydantic.from_tortoise_orm(file_obj)
    
    @classmethod
    async def delete_file(cls, file_id: int) -> bool:
        """Delete file and its physical file"""
        file_obj = await File.get_or_none(id=file_id)
        if not file_obj:
            return False
        
        if os.path.exists(file_obj.file_path):
            os.remove(file_obj.file_path)
        
        # Delete database record
        await file_obj.delete()
        return True
    
    @classmethod
    async def search_files_by_tags(cls, tags: Dict[str, str], skip: int = 0, limit: int = 100) -> List[File_Pydantic]:
        """Search files by tags"""
        query = File.all()
        
        for key, value in tags.items():
            query = query.filter(tags__contains={key: value})
        
        files = await query.offset(skip).limit(limit).order_by("-created_at")
        return [await File_Pydantic.from_tortoise_orm(file) for file in files]


class TagService:
    @classmethod
    async def get_file_tags(cls, file_id: int) -> Dict[str, str]:
        """Get all tags for a file"""
        file_obj = await File.get_or_none(id=file_id)
        if not file_obj:
            return {}
        return file_obj.tags or {}
    
    @classmethod
    async def update_file_tags(cls, file_id: int, tags: Dict[str, str]) -> Dict[str, str]:
        """Update tags for a file"""
        file_obj = await File.get_or_none(id=file_id)
        if not file_obj:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_obj.tags = tags
        await file_obj.save()
        return file_obj.tags
    
    @classmethod
    async def add_tag(cls, file_id: int, key: str, value: str) -> Dict[str, str]:
        """Add a single tag to a file"""
        file_obj = await File.get_or_none(id=file_id)
        if not file_obj:
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_obj.tags:
            file_obj.tags = {}
        
        file_obj.tags[key] = value
        await file_obj.save()
        return file_obj.tags
    
    @classmethod
    async def remove_tag(cls, file_id: int, key: str) -> Dict[str, str]:
        """Remove a tag from a file"""
        file_obj = await File.get_or_none(id=file_id)
        if not file_obj:
            raise HTTPException(status_code=404, detail="File not found")
        
        if file_obj.tags and key in file_obj.tags:
            del file_obj.tags[key]
            await file_obj.save()
        
        return file_obj.tags 