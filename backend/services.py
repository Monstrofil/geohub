from models import File, Tag, File_Pydantic, Tag_Pydantic
from tortoise.expressions import Q
import os
import uuid
import aiofiles
from osgeo import gdal
import geopandas as gpd
from typing import List, Dict, Any, Optional, Tuple
from fastapi import UploadFile, HTTPException


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
    async def create_file(cls, file_data: Dict[str, Any], tags: Dict[str, str] = None, expected_type: str = None) -> File_Pydantic:
        """Create a new file record with automatic type detection"""
        file_info = await cls.save_uploaded_file(file_data["file"])
        
        # Detect file type
        base_file_type = FileTypeService.detect_file_type(
            file_info["file_path"],
        )
        
        # Validate against expected type if provided
        if expected_type and not FileTypeService.validate_file_type(file_info["original_name"], expected_type):
            # Delete the uploaded file if validation fails
            if os.path.exists(file_info["file_path"]):
                os.remove(file_info["file_path"])

            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed for '{expected_type}'. Expected: {', '.join(
                    FileTypeService.get_accepted_extensions(expected_type))}"
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
            tags=file_tags
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