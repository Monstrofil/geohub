from fastapi import APIRouter, UploadFile, File, Form, Body, HTTPException, Depends, Path, Query
from fastapi.responses import FileResponse as FastAPIFileResponse
from typing import List, Dict, Optional, Any
import os
import datetime 
import json
import uuid
from pydantic import BaseModel, ConfigDict

import models
from services import FileService, CollectionsService
from mapserver_service import MapServerService


router = APIRouter(tags=["files"])

# Initialize MapServer service
mapserver_service = MapServerService()


# Unified Pydantic models
class TreeItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: str  # "file" or "collection"
    tags: Dict[str, Any]  # Allow mixed types for file metadata
    created_at: datetime.datetime
    updated_at: datetime.datetime
    path: str

    # Computed properties for backward compatibility
    @property
    def sha1(self) -> str | None:
        """Get SHA1 hash from tags (for files)"""
        return self.tags.get("sha1") if self.type == "file" else None
    
    @property
    def original_name(self) -> str:
        """Get original filename from tags (for files)"""
        return self.tags.get("original_name", self.name) if self.type == "file" else self.name
    
    @property 
    def file_size(self) -> int:
        """Get file size from tags (for files)"""
        return int(self.tags.get("file_size", 0)) if self.type == "file" else 0
    
    @property
    def mime_type(self) -> str:
        """Get MIME type from tags (for files)"""
        return self.tags.get("mime_type", "") if self.type == "file" else ""
    
    @property
    def base_file_type(self) -> str:
        """Get base file type from tags (for files)"""
        return self.tags.get("base_file_type", "raw") if self.type == "file" else ""


class TreeItemListResponse(BaseModel):
    items: list[TreeItemResponse]
    total: int
    skip: int
    limit: int


class TreeItemContentsResponse(BaseModel):
    items: list[TreeItemResponse]
    total: int
    skip: int
    limit: int


class TreeItemUpdateRequest(BaseModel):
    name: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    parent_path: Optional[str] = None


class TreeItemCreateRequest(BaseModel):
    name: str
    type: str  # "file" or "collection"
    tags: Optional[Dict[str, Any]] = None
    parent_path: Optional[str] = "root"


class TreeItemSearchRequest(BaseModel):
    type: Optional[str] = None  # "file" or "collection"
    tags: Optional[Dict[str, Any]] = None
    base_type: Optional[str] = None  # For files: "raster", "vector", "raw"
    collection_path: Optional[str] = None
    skip: int = 0
    limit: int = 100




# Helper functions
async def validate_parent_path(parent_path: str) -> None:
    """Validate that parent path exists"""
    if parent_path and parent_path != "root":
        collection = await CollectionsService.get_collection_by_path(parent_path)
        if not collection:
            raise HTTPException(status_code=404, detail="Parent collection not found")


# ======================
# UNIFIED TREE ITEM ENDPOINTS
# ======================

@router.get("/tree-items", response_model=TreeItemListResponse)
async def list_tree_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type: Optional[str] = Query(None, regex="^(file|collection)$"),
    tags: Optional[str] = Query(None),
    base_type: Optional[str] = Query(None),
    collection_path: Optional[str] = Query(None)
):
    """List tree items with optional filters"""
    filter_tags = {}
    if tags:
        try:
            filter_tags = json.loads(tags)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid tags format")

    # Route to appropriate service based on type
    if type == "file":
        result = await FileService.search_files(
            tags=filter_tags if filter_tags else None,
            base_type=base_type,
            collection_path=collection_path,
            skip=skip,
            limit=limit
        )
        items = [TreeItemResponse.model_validate(f) for f in result["files"]]
        total = result["total"]
    elif type == "collection":
        collections_query = models.TreeItem.filter(type="collection")
        if collection_path:
            collections_query = collections_query.filter(path__contains=collection_path)
        if filter_tags:
            for key, value in filter_tags.items():
                collections_query = collections_query.filter(tags__contains={key: value})
        
        total = await collections_query.count()
        collections = await collections_query.offset(skip).limit(limit).order_by('created_at').all()
        items = [TreeItemResponse.model_validate(c) for c in collections]
    else:
        # Get both files and collections
        if not collection_path or collection_path == "root":
            result_items = await CollectionsService.list_collection_contents("root", skip, limit)
        else:
            result_items = await CollectionsService.list_collection_contents(collection_path, skip, limit)
        
        items = [TreeItemResponse.model_validate(item) for item in result_items]
        total = len(items)  # Since we don't have total counters anymore, use actual count

    return TreeItemListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/tree-items/{item_id}", response_model=TreeItemResponse)
async def get_tree_item(item_id: uuid.UUID):
    """Get tree item by ID"""
    # Try to get as file first, then as collection
    item = await FileService.get_file(str(item_id))
    if not item:
        item = await CollectionsService.get_collection(str(item_id))
    
    if not item:
        raise HTTPException(status_code=404, detail="Tree item not found")
    
    return TreeItemResponse.model_validate(item)


@router.put("/tree-items/{item_id}", response_model=TreeItemResponse)
async def update_tree_item(item_id: uuid.UUID, request: TreeItemUpdateRequest):
    """Update tree item metadata"""
    await validate_parent_path(request.parent_path or "root")

    # Try to update as file first, then as collection
    item = await FileService.update_file(
        str(item_id),
        tags=request.tags,
        new_parent_path=request.parent_path
    )
    
    if not item:
        item = await CollectionsService.update_collection(
            str(item_id),
            name=request.name,
            tags=request.tags,
            new_parent_path=request.parent_path
        )
    
    if not item:
        raise HTTPException(status_code=404, detail="Tree item not found")
    
    return TreeItemResponse.model_validate(item)


@router.delete("/tree-items/{item_id}")
async def delete_tree_item(item_id: uuid.UUID, force: bool = Query(False)):
    """Delete tree item"""
    # Try to delete as file first, then as collection
    success = await FileService.delete_file(str(item_id))
    
    if not success:
        try:
            success = await CollectionsService.delete_collection(str(item_id), force=force)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    if not success:
        raise HTTPException(status_code=404, detail="Tree item not found")
    
    return {"message": "Tree item deleted successfully"}


@router.get("/tree-items/{collection_id}/contents", response_model=TreeItemContentsResponse)
async def get_tree_item_contents(
    collection_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get contents of a collection tree item"""
    # Special case for root
    if str(collection_id) == "root":
        result_items = await CollectionsService.list_collection_contents("root", skip, limit)
    else:
        # Verify collection exists and get its path
        collection = await CollectionsService.get_collection(str(collection_id))
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        result_items = await CollectionsService.list_collection_contents(collection.path, skip, limit)
    
    items = [TreeItemResponse.model_validate(item) for item in result_items]
    
    return TreeItemContentsResponse(
        items=items,
        total=len(items),  # Since we don't have total counters anymore, use actual count
        skip=skip,
        limit=limit
    )


@router.post("/tree-items", response_model=TreeItemResponse)
async def create_tree_item(request: TreeItemCreateRequest):
    """Create a new tree item (collection only - files must be uploaded via /files)"""
    if request.type != "collection":
        raise HTTPException(status_code=400, detail="Only collections can be created via this endpoint. Use /files for file uploads.")
    
    await validate_parent_path(request.parent_path or "root")

    collection_obj = await CollectionsService.create_collection(
        request.name,
        request.tags or {},
        request.parent_path or "root"
    )
    
    return TreeItemResponse.model_validate(collection_obj)


# Special endpoint for root contents
@router.get("/root/contents", response_model=TreeItemContentsResponse)
async def get_root_contents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get contents of the root"""
    result_items = await CollectionsService.list_collection_contents("root", skip, limit)
    
    items = [TreeItemResponse.model_validate(item) for item in result_items]
    
    return TreeItemContentsResponse(
        items=items,
        total=len(items),  # Since we don't have total counters anymore, use actual count
        skip=skip,
        limit=limit
    )


# ======================
# SPECIALIZED ENDPOINTS
# ======================

# File upload, download, and geospatial-specific endpoints
@router.post("/files", response_model=TreeItemResponse)
async def upload_file(
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),
    parent_path: Optional[str] = Form("root")
):
    """Upload a new file"""
    file_tags = {}
    if tags:
        try:
            file_tags = json.loads(tags)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid tags format")

    await validate_parent_path(parent_path or "root")
    file_obj = await FileService.create_file(file, file_tags, parent_path=parent_path or "root")
    return TreeItemResponse.model_validate(file_obj)


@router.get("/files/{file_id}/download")
async def download_file(file_id: uuid.UUID):
    """Download a file"""
    file_obj = await FileService.get_file(str(file_id))
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(file_obj.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FastAPIFileResponse(
        path=file_obj.file_path,
        filename=file_obj.original_name,
        media_type=file_obj.mime_type
    )


# MapServer endpoints (specialized for geospatial files)
@router.get("/files/{file_id}/map")
async def get_file_map(file_id: uuid.UUID):
    """Get a MapServer URL for a GeoTIFF file"""
    file_obj = await FileService.get_file(str(file_id))
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    map_url = mapserver_service.get_map_url(file_obj.name)
    if not map_url:
        raise HTTPException(status_code=400, detail="File type not supported for mapping")
    
    return {"map_url": map_url}


@router.get("/files/{file_id}/extent")
async def get_file_extent(file_id: uuid.UUID):
    """Get the extent (bounding box) of a GeoTIFF file"""
    file_obj = await FileService.get_file(str(file_id))
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    extent = mapserver_service.get_file_extent(file_obj.name)
    if not extent:
        raise HTTPException(status_code=400, detail="File type not supported for extent calculation")
    
    return {"extent": extent}


@router.get("/files/{file_id}/preview")
async def get_file_preview(file_id: uuid.UUID):
    """Get a preview URL for a file (especially GeoTIFF)"""
    file_obj = await FileService.get_file(str(file_id))
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    preview_url = mapserver_service.get_preview_url(file_obj.name)
    if not preview_url:
        raise HTTPException(status_code=400, detail="File type not supported for preview")
    
    return {"preview_url": preview_url}




# MapServer cleanup endpoint
@router.post("/mapserver/cleanup")
async def cleanup_mapserver_configs(max_age_hours: int = 24):
    """Clean up old MapServer configuration files"""
    try:
        mapserver_service.cleanup_old_configs(max_age_hours)
        return {"message": f"Cleaned up MapServer configs older than {max_age_hours} hours"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")