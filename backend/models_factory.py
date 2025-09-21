
import uuid
import os
from pathlib import Path
from typing import Dict
from models import TreeItem, RawFile, GeoRasterFile
from mapserver_service import MapServerService
from services.geo import analyze_raster_file, create_dummy_georeferenced_file
from fastapi import HTTPException


mapserver_service = MapServerService()

async def create_file(file_info: Dict[str, str], tags: Dict[str, str] = None, parent_path: str = "root") -> TreeItem:
    """Create a new raw file record in the database.
    
    Args:
        file_info: Dictionary containing file information (original_name, file_path, file_size, mime_type, name)
        tags: Optional dictionary of tags to apply
        parent_path: Parent path in the tree structure (default: "root")
        
    Returns:
        TreeItem: The created tree item representing the file
    """
    
    # Create LTREE-compatible ID: use 'f' prefix + first 12 chars of UUID hex (no hyphens)
    file_uuid = str(uuid.uuid4()).replace('-', '')[:12]
    file_segment = f"f{file_uuid}"
    
    # Create the path: parent_path.file_segment
    file_ltree_path = f"{parent_path}.{file_segment}"

    user_tags = tags or {}

    # Create RawFile (minimal model)
    raw_file = await RawFile.create(
        original_name=file_info["original_name"],
        file_path=file_info["file_path"],
        file_size=file_info["file_size"],
        mime_type=file_info["mime_type"]
    )
    
    # Create TreeItem
    file_obj = await TreeItem.create(
        name=file_info["name"],
        object_type="raw_file",
        object_id=raw_file.id,
        path=file_ltree_path,
        tags=user_tags
    )
    
    return file_obj


async def create_geo_file(file_info: Dict[str, str], tags: Dict[str, str] = None, parent_path: str = "root") -> TreeItem:
    """Create a new georeferenced raster file record in the database.
    
    Args:
        file_info: Dictionary containing file information (original_name, file_path, file_size, mime_type, name)
        tags: Optional dictionary of tags to apply
        parent_path: Parent path in the tree structure (default: "root")
        
    Returns:
        TreeItem: The created tree item representing the geo file
    """
    
    # Create LTREE-compatible ID: use 'f' prefix + first 12 chars of UUID hex (no hyphens)
    file_uuid = str(uuid.uuid4()).replace('-', '')[:12]
    file_segment = f"f{file_uuid}"
    
    # Create the path: parent_path.file_segment
    file_ltree_path = f"{parent_path}.{file_segment}"

    user_tags = tags or {}

    map_config_path = mapserver_service._create_map_config(file_info["file_path"])

    # Create GeoRasterFile (minimal model)
    geo_raster = await GeoRasterFile.create(
        original_name=file_info["original_name"],
        file_path=file_info["file_path"],
        original_file_path=None,
        file_size=file_info["file_size"],
        mime_type=file_info["mime_type"],
        map_config_path=map_config_path
    )
    

    # Create TreeItem
    file_obj = await TreeItem.create(
        name=file_info["name"],
        object_type="geo_raster_file",
        object_id=geo_raster.id,
        path=file_ltree_path,
        tags=user_tags
    )

    return file_obj


async def convert_to_geo_raster(raw_file: RawFile, upload_dir: str = "uploads") -> TreeItem:
    """Convert a RawFile to GeoRasterFile and create dummy georeferenced TIF if needed"""
        
    # Analyze the raster file to make sure it's GDAL compatible and get dimensions
    analysis = analyze_raster_file(raw_file.file_path)
    if not analysis["gdal_compatible"]:
        raise HTTPException(status_code=400, detail=f"File is not GDAL compatible: {analysis.get('error', 'Unknown error')}")
    
    # Get image dimensions from analysis
    image_width = analysis["width"]
    image_height = analysis["height"]
    image_bands = analysis["bands"]
    
    dummy_georeferenced_file_path = create_dummy_georeferenced_file(raw_file.file_path, upload_dir)
    
    map_config_path = mapserver_service._create_map_config(dummy_georeferenced_file_path)
    geo_raster = await GeoRasterFile.create(
        original_name=raw_file.original_name,
        file_path=dummy_georeferenced_file_path,
        original_file_path=dummy_georeferenced_file_path,
        file_size=raw_file.file_size,
        mime_type=raw_file.mime_type,
        image_width=image_width,
        image_height=image_height,
        image_bands=image_bands,
        map_config_path=map_config_path
    )
    await geo_raster.save()
    await raw_file.delete()
    
    if os.path.exists(raw_file.file_path):
        os.remove(raw_file.file_path)
    
    return geo_raster