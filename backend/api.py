from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Path, Query, Depends
from fastapi.responses import FileResponse as FastAPIFileResponse
from typing import List, Dict, Optional, Any
import os
import datetime 
import json
import uuid
import shutil
from pydantic import BaseModel, ConfigDict

import models
from models import TreeItem, User
from services import FileService, CollectionsService
from mapserver_service import MapServerService
from georeferencing_service import GeoreferencingService, ControlPoint
from auth import get_current_user, get_current_user_optional, require_permission, Permission


router = APIRouter(tags=["files"])

# Initialize services
mapserver_service = MapServerService()
# Use uploads directory for temp files to ensure MapServer can access them
georeferencing_service = GeoreferencingService(uploads_dir="./uploads", temp_dir="./uploads")


# Unified Pydantic models
class TreeItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: str  # "file" or "collection"
    object_type: str
    tags: Dict[str, Any]  # Allow mixed types for file metadata
    created_at: datetime.datetime
    updated_at: datetime.datetime
    path: str

    permissions: int
    owner_user_id: uuid.UUID | None
    owner_group_id: uuid.UUID | None

class TreeItemDetails(TreeItemResponse):
    object_details: models.KnownTreeItemTypes | None = None


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


# Georeferencing-specific models
class ControlPointModel(BaseModel):
    image_x: float
    image_y: float
    world_x: float
    world_y: float


class ControlPointsRequest(BaseModel):
    control_points: List[ControlPointModel]
    target_srs: str = "EPSG:4326"


class GeoreferencingApplyRequest(BaseModel):
    control_points: List[ControlPointModel]
    control_points_srs: str = "EPSG:4326"
    metadata: Optional[Dict[str, Any]] = None






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
        collections_query = models.TreeItem.filter(object_type="collection")
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


@router.get("/tree-items/{item_id}", response_model=TreeItemDetails)
async def get_tree_item(
    item_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get tree item by ID"""
    # Try to get as file first, then as collection
    item = await models.TreeItem.filter(id=str(item_id)).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Tree item not found")
    
    await require_permission(item, current_user, Permission.READ)
    
    response = TreeItemDetails.model_validate(item)
    
    # Get the actual object and convert to appropriate Pydantic model
    obj = await item.object
    if isinstance(obj, models.RawFile):
        response.object_details = models.RawFile_Pydantic.model_validate(obj)
    elif isinstance(obj, models.GeoRasterFile):
        response.object_details = models.GeoRasterFile_Pydantic.model_validate(obj)
    elif isinstance(obj, models.Collection):
        response.object_details = models.Collection_Pydantic.model_validate(obj)
    else:
        response.object_details = None
    
    return response


@router.put("/tree-items/{item_id}", response_model=TreeItemResponse)
async def update_tree_item(
    item_id: uuid.UUID,
    request: TreeItemUpdateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Update tree item metadata"""
    await validate_parent_path(request.parent_path or "root")

    # First check if item exists and user has write permission
    item = await models.TreeItem.filter(id=str(item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Tree item not found")
    
    # Check write permission
    await require_permission(item, current_user, Permission.WRITE)

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
async def delete_tree_item(
    item_id: uuid.UUID,
    force: bool = Query(False),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Delete tree item"""
    # First check if item exists and user has write permission
    item = await models.TreeItem.filter(id=str(item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Tree item not found")
    
    # Check write permission
    await require_permission(item, current_user, Permission.WRITE)
    
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

        await require_permission(collection, current_user, Permission.READ)
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

    # TODO: Uncomment this when we have a way to get the current user
    # await require_permission(collection, current_user, Permission.WRITE)

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
    parent_path: Optional[str] = Form("root"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Upload a new file with automatic georeferencing detection
    
    If the uploaded file is already georeferenced (has projection and geotransform),
    it will be saved as a GeoRasterFile. Otherwise, it will be saved as a RawFile.
    """
    file_tags = {}
    if tags:
        try:
            file_tags = json.loads(tags)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid tags format")

    await validate_parent_path(parent_path or "root")
    file_obj = await FileService.create_file(file, file_tags, parent_path=parent_path or "root")
    
    # Set ownership if user is authenticated
    if current_user:
        file_obj.owner_user_id = current_user.id
        # Default permissions: owner can read/write, group can read, others can read
        file_obj.permissions = 0o644
        await file_obj.save()
    
    return TreeItemResponse.model_validate(file_obj)


@router.post("/tree-items/{item_id}/probe")
async def probe_tree_item(item_id: uuid.UUID):
    """Probe a tree item to check if it can be georeferenced with GDAL"""
    result = await FileService.probe_tree_item(str(item_id))
    return result


@router.post("/tree-items/{item_id}/convert-to-geo-raster", response_model=TreeItemResponse)
async def convert_to_geo_raster(item_id: uuid.UUID):
    """Convert a RawFile to GeoRasterFile for georeferencing"""
    file_obj = await FileService.convert_to_geo_raster(str(item_id))
    return TreeItemResponse.model_validate(file_obj)


@router.get("/files/{file_id}/download")
async def download_file(file_id: uuid.UUID):
    """Download a file"""
    # Look for TreeItem by ID
    tree_item = await TreeItem.get_or_none(id=file_id)
    if not tree_item:
        raise HTTPException(status_code=404, detail="TreeItem not found")
    
    # Get object of that tree item
    try:
        obj = await tree_item.get_object()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Error getting object: {str(e)}")
    
    # Check if object has get_download_path method
    if not hasattr(obj, 'get_download_path'):
        raise HTTPException(status_code=400, detail="Download is not available for this item")
    
    # Get download path
    download_path = obj.get_download_path()
    
    if not os.path.exists(download_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FastAPIFileResponse(
        path=download_path,
        filename=obj.original_name,
        media_type=obj.mime_type
    )


# MapServer endpoints (specialized for geospatial files)
@router.get("/files/{file_id}/map")
async def get_file_map(file_id: uuid.UUID):
    """Get a MapServer URL for a GeoTIFF file"""
    file_obj = await FileService.get_file(str(file_id))
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Use the actual file path (which may be georeferenced version) instead of just the name
    file_path = await file_obj.get_file_path()
    if not file_path:
        raise HTTPException(status_code=400, detail="File path not found")
    
    # Extract filename from the full path
    filename = os.path.basename(file_path)
    
    map_url = mapserver_service.get_map_url(filename)
    if not map_url:
        raise HTTPException(status_code=400, detail="File type not supported for mapping")
    
    return {"map_url": map_url}


@router.get("/files/{file_id}/extent")
async def get_file_extent(file_id: uuid.UUID):
    """Get the extent (bounding box) of a GeoTIFF file"""
    file_obj = await FileService.get_file(str(file_id))
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Use the actual file path (which may be georeferenced version) instead of just the name
    file_path = await file_obj.get_file_path()
    if not file_path:
        raise HTTPException(status_code=400, detail="File path not found")
    
    # Extract filename from the full path
    filename = os.path.basename(file_path)
    
    extent = mapserver_service.get_file_extent(filename)
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


# ======================
# GEOREFERENCING ENDPOINTS
# ======================




@router.post("/files/{file_id}/validate-control-points")
async def validate_control_points(file_id: uuid.UUID, request: ControlPointsRequest):
    """Validate control points and return accuracy statistics"""
    file_obj = await FileService.get_file(str(file_id))
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Convert Pydantic models to ControlPoint objects
        control_points = [
            ControlPoint(cp.image_x, cp.image_y, cp.world_x, cp.world_y)
            for cp in request.control_points
        ]
        
        # Validate control points
        validation_results = georeferencing_service.validate_control_points(control_points)
        
        return validation_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating control points: {str(e)}")


@router.post("/files/{file_id}/apply-georeferencing")
async def apply_georeferencing(file_id: uuid.UUID, request: GeoreferencingApplyRequest):
    """Apply georeferencing to a file and update the database"""
    tree_obj = await models.TreeItem.get_or_none(id=file_id, object_type="geo_raster_file")
    if not tree_obj:
        raise HTTPException(status_code=404, detail="File not found")
    

    geo_raster_file = await tree_obj.get_object()
    file_path = geo_raster_file.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Convert Pydantic models to ControlPoint objects
    control_points = [
        ControlPoint(cp.image_x, cp.image_y, cp.world_x, cp.world_y)
        for cp in request.control_points
    ]
        
    
    try:
        # Validate control points
        validation_results = georeferencing_service.validate_control_points(control_points)
        
        if not validation_results['valid']:
            raise HTTPException(status_code=400, detail=f"Invalid control points: {validation_results['errors']}")
        
        # Create the final georeferenced file
        georeferenced_path = georeferencing_service.warp_image_with_control_points(
            file_path,
            control_points,
            request.control_points_srs
        )
        
        # Replace with georeferenced
        os.rename(georeferenced_path, file_path) 
        
        geo_raster_file.file_path = file_path
        await geo_raster_file.save()
        
        # Update user metadata if provided
        user_metadata = request.metadata or {}
        updated_file = await FileService.update_file(str(file_id), tags=user_metadata)
        
        
        return {
            "message": "Georeferencing applied successfully",
            "file": TreeItemResponse.model_validate(updated_file),
            "validation_results": validation_results
        }
        
    except Exception as e:
        # If something went wrong, try to restore the backup
        try:
            file_path = await file_obj.get_file_path()
            backup_path = file_path + ".backup"
            if os.path.exists(backup_path):
                shutil.move(backup_path, file_path)
        except:
            pass
        
        raise HTTPException(status_code=500, detail=f"Error applying georeferencing: {str(e)}")


@router.post("/georeferencing/cleanup")
async def cleanup_georeferencing_temp_files(max_age_hours: int = 24):
    """Clean up temporary georeferencing files"""
    try:
        georeferencing_service.cleanup_temp_files(max_age_hours)
        return {"message": f"Cleaned up georeferencing temp files older than {max_age_hours} hours"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")