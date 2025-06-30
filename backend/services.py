from models import File, Tag, File_Pydantic, Tag_Pydantic, Tree, TreeEntry, Commit, Ref, calculate_file_obj_hash
from tortoise.expressions import Q
import os
import uuid
import aiofiles
from osgeo import gdal
import geopandas as gpd
from typing import List, Dict, Any, Optional, Tuple
from fastapi import UploadFile, HTTPException
import hashlib
from datetime import datetime, timezone
import json
import random
from git_service import add_file, update_file, delete_file


class FileTypeService:
    """Service for detecting file types using GDAL and GeoPandas"""
    
    @classmethod
    def detect_file_type(cls, file_path: str) -> str:
        """
        Detect the base file type using GDAL and GeoPandas
        
        Returns:
            str: base_file_type
        """
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise RuntimeError("Uploaded file is missing: check disk storage")
        
        # Try to detect as raster using GDAL
        if cls._is_raster(file_path):
            return "raster"
        
        # Try to detect as vector using GeoPandas
        if cls._is_vector(file_path):
            return "vector"
        
        # If neither, it's a raw file
        return "raw"

    
    @classmethod
    def _is_raster(cls, file_path: str) -> bool:
        """
        Check if file is a raster using GDAL
        """
        dataset = gdal.Open(file_path)
        if dataset is None:
            return False
        
        # Check if it has geotransform (extent)
        geotransform = dataset.GetGeoTransform()
        if geotransform is None:
            return False
        
        return True
    
    @classmethod
    def _is_vector(cls, file_path: str) -> bool:
        """
        Check if file is a vector using GeoPandas
        """
        try:
            gdf = gpd.read_file(file_path)
            return True
        except Exception as e:
            print(f"Error checking vector with GeoPandas: {e}")
            return False
    
    @classmethod
    def validate_file_type(cls, filename: str, expected_type: str) -> bool:
        """
        Validate if a file matches the expected base type
        
        Args:
            filename: The filename to check
            expected_type: Expected base type ('raster', 'vector', 'raw')
        
        Returns:
            bool: True if file type matches expected type
        """
        if not filename:
            return False
        
        # For validation, we need to actually check the file
        file_path = os.path.join(FileService.UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            return False
        
        if expected_type == "raster":
            return cls._is_raster(file_path)
        elif expected_type == "vector":
            return cls._is_vector(file_path)
        elif expected_type == "raw":
            # Raw accepts anything that's not raster or vector
            return not cls._is_raster(file_path) and not cls._is_vector(file_path)
        else:
            return False


class FileService:
    UPLOAD_DIR = "uploads"
    
    @classmethod
    async def ensure_upload_dir(cls):
        """Ensure upload directory exists"""
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)
    
    @classmethod
    async def save_uploaded_file(cls, file: UploadFile, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Save uploaded file to disk and return file info"""
        await cls.ensure_upload_dir()
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(cls.UPLOAD_DIR, unique_filename)
        
        # Save file and calculate sha1
        content = await file.read()
        tags = tags or {}
        tags_json = json.dumps(tags, sort_keys=True, separators=(",", ":"))
        sha1 = hashlib.sha1(content + tags_json.encode('utf-8')).hexdigest()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return {
            "original_name": file.filename,
            "name": unique_filename,
            "file_path": file_path,
            "file_size": len(content),
            "mime_type": file.content_type or "application/octet-stream",
            "sha1": sha1
        }
    
    @classmethod
    async def create_file(cls, file_data: Dict[str, Any], tags: Dict[str, str] = None, expected_type: str = None) -> File_Pydantic:
        """Create a new file record with automatic type detection and versioning"""
        file_info = await cls.save_uploaded_file(file_data["file"], tags)
        
        # Detect file type
        base_file_type = FileTypeService.detect_file_type(file_info["file_path"])
        
        # Validate against expected type if provided
        if expected_type and not FileTypeService.validate_file_type(file_info["original_name"], expected_type):
            # Delete the uploaded file if validation fails
            if os.path.exists(file_info["file_path"]):
                os.remove(file_info["file_path"])
            expected = ', '.join(FileTypeService.get_accepted_extensions(expected_type))
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed for '{expected_type}'. Expected: {expected}"
            )
        
        # Prepare tags with type information
        file_tags = tags or {}
        
        # Create file record
        file_obj = await File.create(
            name=file_info["name"],
            original_name=file_info["original_name"],
            file_path=file_info["file_path"],
            file_size=file_info["file_size"],
            mime_type=file_info["mime_type"],
            base_file_type=base_file_type,
            tags=file_tags,
            sha1=file_info["sha1"]
        )

        await add_file(file_obj, message=f"Add file {file_obj.name}")
        
        return await File_Pydantic.from_tortoise_orm(file_obj)
    
    @classmethod
    async def get_file(cls, file_id: int) -> Optional[File_Pydantic]:
        """Get file by ID"""
        file_obj = await File.get_or_none(id=file_id)
        if file_obj:
            return await File_Pydantic.from_tortoise_orm(file_obj)
        return None
    
    @classmethod
    async def list_files(cls, commit: str, skip: int = 0, limit: int = 100) -> List[File_Pydantic]:
        """List files for a specific commit (commit is required)"""
        if not commit:
            return []
        commit_obj = await Commit.get_or_none(id=commit)
        if not commit_obj:
            return []
        tree = await commit_obj.tree
        if not tree:
            return []
        entries = await TreeEntry.filter(sha1__in=tree.entries, object_type="file")
        file_ids = [entry.object_id for entry in entries]
        files = await File.filter(id__in=file_ids).offset(skip).limit(limit).order_by("-created_at")
        return [await File_Pydantic.from_tortoise_orm(file) for file in files]
    
    @classmethod
    async def update_file_tags(cls, file_id: int, tags: Dict[str, str]) -> Optional[File_Pydantic]:
        """Update file tags and create a new commit"""
        orig_file_obj = await File.get_or_none(id=file_id)
        if not orig_file_obj:
            return None
        
        orig_file_obj_id = orig_file_obj.id
        
        # Copy file record, assign new tags
        new_file_obj = orig_file_obj
        new_file_obj.id = None
        new_file_obj.tags = tags
        new_file_obj.sha1 = calculate_file_obj_hash(new_file_obj)
        await new_file_obj.save()

        await update_file(orig_file_obj_id, new_file_obj, message=f"Update tags for file {new_file_obj.name}")

        return new_file_obj.id
    
    @classmethod
    async def delete_file(cls, file_id: int) -> bool:
        """Delete file and its physical file, and create a new commit"""
        file_obj = await File.get_or_none(id=file_id)
        if not file_obj:
            return False
        
        # Remove file from disk
        if os.path.exists(file_obj.file_path):
            os.remove(file_obj.file_path)
        
        await delete_file(file_obj, message=f"Delete file {file_obj.name}")
        await file_obj.delete()

        return True
    
    @classmethod
    async def search_files_by_tags(cls, tags: Dict[str, str], base_type: str = None, skip: int = 0, limit: int = 100) -> List[File_Pydantic]:
        """Search files by tags and optionally filter by base type"""
        query = File.all()
        
        # Filter by base type if provided
        if base_type:
            query = query.filter(base_file_type=base_type)
        
        # Filter by tags
        for key, value in tags.items():
            query = query.filter(tags__contains={key: value})
        
        files = await query.offset(skip).limit(limit).order_by("-created_at")
        return [await File_Pydantic.from_tortoise_orm(file) for file in files]
