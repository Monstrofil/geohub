from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse as FastAPIFileResponse
from typing import List, Dict, Optional
import os

import json
from pydantic import BaseModel

from models import File_Pydantic
from services import FileService, TagService, FileTypeService
from mapserver_service import MapServerService


router = APIRouter(tags=["files"])

# Initialize MapServer service
mapserver_service = MapServerService()


# Pydantic models for request/response
class FileResponse(BaseModel):
    id: int
    name: str
    original_name: str
    file_size: int
    mime_type: str
    base_file_type: str
    tags: Dict[str, str]
    created_at: str
    updated_at: str


class FileListResponse(BaseModel):
    files: List[FileResponse]
    total: int
    skip: int
    limit: int


class TagUpdateRequest(BaseModel):
    tags: Dict[str, str]


class FileSearchRequest(BaseModel):
    tags: Dict[str, str]
    base_type: Optional[str] = None
    skip: int = 0
    limit: int = 100


# File endpoints
@router.post("/files/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),
    expected_type: Optional[str] = Form(None)
):
    """Upload a new file with optional tags and type validation"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Parse tags if provided
    file_tags = {}
    if tags:
        try:
            file_tags = json.loads(tags)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid tags format")
    
    # Validate expected type if provided
    if expected_type and expected_type not in ["raster", "vector", "raw"]:
        raise HTTPException(status_code=400, detail="Invalid expected_type. Must be 'raster', 'vector', or 'raw'")
    
    # Create file
    file_data = {"file": file}
    file_obj = await FileService.create_file(file_data, file_tags, expected_type)
    
    return FileResponse(
        id=file_obj.id,
        name=file_obj.name,
        original_name=file_obj.original_name,
        file_size=file_obj.file_size,
        mime_type=file_obj.mime_type,
        base_file_type=file_obj.base_file_type,
        tags=file_obj.tags,
        created_at=file_obj.created_at.isoformat(),
        updated_at=file_obj.updated_at.isoformat()
    )


@router.get("/files", response_model=FileListResponse)
async def list_files(skip: int = 0, limit: int = 100):
    """List all files with pagination"""
    files = await FileService.list_files(skip=skip, limit=limit)
    
    return FileListResponse(
        files=[
            FileResponse(
                id=file.id,
                name=file.name,
                original_name=file.original_name,
                file_size=file.file_size,
                mime_type=file.mime_type,
                base_file_type=file.base_file_type,
                tags=file.tags,
                created_at=file.created_at.isoformat(),
                updated_at=file.updated_at.isoformat()
            ) for file in files
        ],
        total=len(files),  # In a real app, you'd get total count separately
        skip=skip,
        limit=limit
    )


@router.get("/files/{file_id}", response_model=FileResponse)
async def get_file(file_id: int):
    """Get a specific file by ID"""
    file_obj = await FileService.get_file(file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        id=file_obj.id,
        name=file_obj.name,
        original_name=file_obj.original_name,
        file_size=file_obj.file_size,
        mime_type=file_obj.mime_type,
        base_file_type=file_obj.base_file_type,
        tags=file_obj.tags,
        created_at=file_obj.created_at.isoformat(),
        updated_at=file_obj.updated_at.isoformat()
    )


@router.get("/files/{file_id}/download")
async def download_file(file_id: int):
    """Download a file"""
    file_obj = await FileService.get_file(file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(file_obj.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FastAPIFileResponse(
        path=file_obj.file_path,
        filename=file_obj.original_name,
        media_type=file_obj.mime_type
    )


@router.delete("/files/{file_id}")
async def delete_file(file_id: int):
    """Delete a file"""
    success = await FileService.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"message": "File deleted successfully"}


@router.post("/files/search", response_model=FileListResponse)
async def search_files(request: FileSearchRequest):
    """Search files by tags"""
    files = await FileService.search_files_by_tags(
        tags=request.tags,
        base_type=request.base_type,
        skip=request.skip,
        limit=request.limit
    )
    
    return FileListResponse(
        files=[
            FileResponse(
                id=file.id,
                name=file.name,
                original_name=file.original_name,
                file_size=file.file_size,
                mime_type=file.mime_type,
                base_file_type=file.base_file_type,
                tags=file.tags,
                created_at=file.created_at.isoformat(),
                updated_at=file.updated_at.isoformat()
            ) for file in files
        ],
        total=len(files),
        skip=request.skip,
        limit=request.limit
    )


# Tag endpoints
@router.get("/files/{file_id}/tags")
async def get_file_tags(file_id: int):
    """Get all tags for a file"""
    tags = await TagService.get_file_tags(file_id)
    return {"tags": tags}


@router.put("/files/{file_id}/tags")
async def update_file_tags(file_id: int, request: TagUpdateRequest):
    """Update all tags for a file"""
    tags = await TagService.update_file_tags(file_id, request.tags)
    return {"tags": tags}


@router.post("/files/{file_id}/tags/{key}")
async def add_tag(file_id: int, key: str, value: str):
    """Add a single tag to a file"""
    tags = await TagService.add_tag(file_id, key, value)
    return {"tags": tags}


@router.delete("/files/{file_id}/tags/{key}")
async def remove_tag(file_id: int, key: str):
    """Remove a tag from a file"""
    tags = await TagService.remove_tag(file_id, key)
    return {"tags": tags}


# MapServer endpoints
@router.get("/files/{file_id}/preview")
async def get_file_preview(file_id: int):
    """Get a preview URL for a file (especially GeoTIFF)"""
    file_obj = await FileService.get_file(file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    preview_url = mapserver_service.get_preview_url(file_obj.name)
    if not preview_url:
        raise HTTPException(status_code=400, detail="File type not supported for preview")
    
    return {"preview_url": preview_url}


@router.get("/files/{file_id}/map")
async def get_file_map(file_id: int):
    """Get a MapServer URL for a GeoTIFF file"""
    file_obj = await FileService.get_file(file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    map_url = mapserver_service.get_map_url(file_obj.name)
    if not map_url:
        raise HTTPException(status_code=400, detail="File type not supported for mapping")
    
    return {"map_url": map_url}


@router.get("/files/{file_id}/extent")
async def get_file_extent(file_id: int):
    """Get the extent (bounding box) of a GeoTIFF file"""
    file_obj = await FileService.get_file(file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    extent = mapserver_service.get_file_extent(file_obj.name)
    if not extent:
        raise HTTPException(status_code=400, detail="File type not supported for extent calculation")
    
    return {"extent": extent}


@router.post("/mapserver/cleanup")
async def cleanup_mapserver_configs(max_age_hours: int = 24):
    """Clean up old MapServer configuration files"""
    try:
        mapserver_service.cleanup_old_configs(max_age_hours)
        return {"message": f"Cleaned up MapServer configs older than {max_age_hours} hours"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}") 