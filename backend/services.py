from models import File, File_Pydantic, Tree, TreeEntry, Commit, Ref, calculate_file_obj_hash
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


def detect_file_type(file_path: str) -> str:
    """
    Detect the base file type using GDAL and GeoPandas
    
    Returns:
        str: base_file_type
    """
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise RuntimeError("Uploaded file is missing: check disk storage")
    
    # Try to detect as raster using GDAL
    if _is_raster(file_path):
        return "raster"
    
    # Try to detect as vector using GeoPandas
    if _is_vector(file_path):
        return "vector"
    
    # If neither, it's a raw file
    return "raw"


def _is_raster(file_path: str) -> bool:
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


def _is_vector(file_path: str) -> bool:
    """
    Check if file is a vector using GeoPandas
    """
    try:
        gdf = gpd.read_file(file_path)
        return True
    except Exception as e:
        print(f"Error checking vector with GeoPandas: {e}")
        return False


def validate_file_type(filename: str, expected_type: str) -> bool:
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
        return _is_raster(file_path)
    elif expected_type == "vector":
        return _is_vector(file_path)
    elif expected_type == "raw":
        # Raw accepts anything that's not raster or vector
        return not _is_raster(file_path) and not _is_vector(file_path)
    else:
        return False


class CollectionsService:
    @classmethod
    async def create_collection(cls, name: str, tags: dict):
        tree_obj = await Tree.create(
            name=name,
            tags=tags,
            entries=[],
        )
        
        return tree_obj

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
    async def create_file(cls, uploaded_file, tags: Dict[str, str] = None, expected_type: str = None) -> File_Pydantic:
        """Create a new file record with automatic type detection and versioning"""
        file_info = await cls.save_uploaded_file(uploaded_file, tags)
        
        # Detect file type
        base_file_type = detect_file_type(file_info["file_path"])
        
        # Validate against expected type if provided
        if expected_type and not validate_file_type(file_info["original_name"], expected_type):
            # Delete the uploaded file if validation fails
            if os.path.exists(file_info["file_path"]):
                os.remove(file_info["file_path"])
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed for '{expected_type}'"
            )

        file_tags = tags or {}

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
        
        return file_obj
    
    @classmethod
    async def get_file(cls, file_id: int) -> Optional[File_Pydantic]:
        """Get file by ID"""
        file_obj = await File.get_or_none(id=file_id)
        if file_obj:
            return await File_Pydantic.from_tortoise_orm(file_obj)
        return None
    
