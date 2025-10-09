from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Path, Query, Depends, Request
from fastapi.responses import FileResponse as FastAPIFileResponse, Response
from typing import List, Dict, Optional, Any
import os
import datetime 
import json
import uuid
import shutil
import aiofiles
from pathlib import Path
from pydantic import BaseModel, ConfigDict

import models
import models_factory
from models import TreeItem, User, ChunkedUploadSession
from services import FileService, CollectionsService, georeference
from services.geo import analyze_raster_file
from mapserver_service import MapServerService
from auth import get_current_user, get_current_user_optional, require_permission, Permission


router = APIRouter(tags=["files"])

# Initialize services
mapserver_service = MapServerService()


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
    leaf: TreeItemResponse


class TreeItemContentsResponse(BaseModel):
    items: list[TreeItemResponse]
    total: int
    skip: int
    limit: int


class TreeItemUpdateRequest(BaseModel):
    name: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    parent_path: Optional[str] = None
    permissions: Optional[int] = None


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


# Chunked upload models
class ChunkedUploadInitRequest(BaseModel):
    filename: str
    file_size: int
    mime_type: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    parent_path: Optional[str] = "root"


class ChunkedUploadInitResponse(BaseModel):
    upload_id: str
    chunk_size: int
    total_chunks: int


class ChunkedUploadChunkRequest(BaseModel):
    upload_id: str
    chunk_number: int
    chunk_data: bytes


class ChunkedUploadCompleteRequest(BaseModel):
    upload_id: str
    checksum: Optional[str] = None

# ======================
# UNIFIED TREE ITEM ENDPOINTS
# ======================

@router.get("/tree-items", response_model=TreeItemListResponse)
async def list_tree_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    collection_path: Optional[str] = Query("root"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List tree items with optional filters"""
    collection = await CollectionsService.get_collection_by_path(collection_path)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    await require_permission(collection, current_user, Permission.READ)

    result_items = await CollectionsService.list_collection_contents(collection_path, skip, limit)
    
    items = [TreeItemResponse.model_validate(item) for item in result_items]
    total = len(items)  # Since we don't have total counters anymore, use actual count

    return TreeItemListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        leaf=TreeItemResponse.model_validate(collection)
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
    collection = await CollectionsService.get_collection_by_path(request.parent_path or "root")
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    await require_permission(collection, current_user, Permission.WRITE)

    # First check if item exists and user has write permission
    item = await models.TreeItem.filter(id=str(item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Tree item not found")
    
    await require_permission(item, current_user, Permission.WRITE)
    
    if request.permissions is not None:
        item.permissions = request.permissions
    
    if request.name is not None:
        item.name = request.name
    
    if request.tags is not None:
        item.tags = request.tags
    
    if request.parent_path is not None:
        # Update the item's path based on the new parent
        old_path = item.path
        path_parts = old_path.split('.')
        item_segment = path_parts[-1]  # Keep the same item ID segment
        
        new_path = f"{request.parent_path}.{item_segment}"
        
        item.path = new_path
        
        # update all descendant paths
        from tortoise import connections
        connection = connections.get("default")
        
        # Update all tree items (both files and collections) that are descendants
        await connection.execute_query(
            "UPDATE tree_items SET path = $1 || subpath(path, nlevel($2)) WHERE path <@ $2 AND path != $2",
            [new_path, old_path]
        )
    
    await item.save()
    
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
    
    # TODO: delete only tree item and keep objects as orphans
    #       but this requires implementation of check "is_deletable"
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


@router.post("/tree-items", response_model=TreeItemResponse)
async def create_tree_item(request: TreeItemCreateRequest, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Create a new tree item (collection only - files must be uploaded via /files)"""
    if request.type != "collection":
        raise HTTPException(status_code=400, detail="Only collections can be created via this endpoint. Use /files for file uploads.")
    
    collection = await CollectionsService.get_collection_by_path(request.parent_path or "root")
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    await require_permission(collection, current_user, Permission.WRITE)

    collection_obj = await CollectionsService.create_collection(
        request.name,
        request.tags or {},
        request.parent_path or "root"
    )
    
    return TreeItemResponse.model_validate(collection_obj)


# ======================
# SPECIALIZED ENDPOINTS
# ======================

# File upload, download, and geospatial-specific endpoints
@router.post("/files", response_model=TreeItemResponse)
async def upload_file(
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),
    parent_path: Optional[str] = Form("root"),
    current_user: Optional[User] = Depends(get_current_user)
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

    collection = await CollectionsService.get_collection_by_path(parent_path or "root")
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    await require_permission(collection, current_user, Permission.WRITE)

    file_info = await FileService.save_uploaded_file(file)

    analysis = analyze_raster_file(file_info["file_path"])
    is_georeferenced = analysis.get("is_georeferenced", False)

    if is_georeferenced:
        file_obj = await models_factory.create_geo_file(
            file_info, file_tags, parent_path=parent_path or "root")
    else:
        file_obj = await models_factory.create_file(
            file_info, file_tags, parent_path=parent_path or "root")
    

    file_obj.owner_user_id = current_user.id
    file_obj.permissions = 0o644
    await file_obj.save()
    
    return TreeItemResponse.model_validate(file_obj)


# ======================
# CHUNKED UPLOAD ENDPOINTS
# ======================

@router.post("/files/chunked/init", response_model=ChunkedUploadInitResponse)
async def init_chunked_upload(
    request: ChunkedUploadInitRequest,
    current_user: Optional[User] = Depends(get_current_user)
):
    """Initialize a chunked upload session"""
    collection = await CollectionsService.get_collection_by_path(request.parent_path or "root")
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    await require_permission(collection, current_user, Permission.WRITE)

    # Generate upload ID and calculate chunks
    upload_id = str(uuid.uuid4())
    chunk_size = 75 * 1024 * 1024  # 100MB chunks
    total_chunks = (request.file_size + chunk_size - 1) // chunk_size

    # Create temp directory for chunks
    temp_dir = os.path.join("uploads", "temp", upload_id)
    os.makedirs(temp_dir, exist_ok=True)

    # Set expiration time (24 hours from now)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)

    # Create upload session in database
    upload_session = await ChunkedUploadSession.create(
        upload_id=upload_id,
        user=current_user,
        filename=request.filename,
        file_size=request.file_size,
        mime_type=request.mime_type,
        tags=request.tags or {},
        parent_path=request.parent_path or "root",
        chunk_size=chunk_size,
        total_chunks=total_chunks,
        chunks_received=[],
        temp_dir=temp_dir,
        expires_at=expires_at
    )

    return ChunkedUploadInitResponse(
        upload_id=upload_id,
        chunk_size=chunk_size,
        total_chunks=total_chunks
    )


@router.post("/files/chunked/upload")
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_number: int = Form(...),
    chunk_data: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Upload a single chunk"""
    # Get upload session from database
    session = await ChunkedUploadSession.get_or_none(upload_id=upload_id)
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
    
    # Check if session belongs to current user
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if session has expired
    if session.is_expired():
        raise HTTPException(status_code=410, detail="Upload session has expired")
    
    if chunk_number < 0 or chunk_number >= session.total_chunks:
        raise HTTPException(status_code=400, detail="Invalid chunk number")
    
    # Save chunk
    chunk_path = os.path.join(session.temp_dir, f"chunk_{chunk_number}")
    content = await chunk_data.read()
    
    async with aiofiles.open(chunk_path, 'wb') as f:
        await f.write(content)
    
    # Mark chunk as received in database
    session.add_chunk(chunk_number)
    await session.save()
    
    return {
        "message": "Chunk uploaded successfully",
        "chunk_number": chunk_number,
        "chunks_received": len(session.chunks_received),
        "total_chunks": session.total_chunks
    }


@router.post("/files/chunked/complete", response_model=TreeItemResponse)
async def complete_chunked_upload(
    request: ChunkedUploadCompleteRequest,
    current_user: Optional[User] = Depends(get_current_user)
):
    """Complete the chunked upload and create the file"""
    # Get upload session from database
    session = await ChunkedUploadSession.get_or_none(upload_id=request.upload_id)
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
    
    # Check if session belongs to current user
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if session has expired
    if session.is_expired():
        # Clean up expired session
        shutil.rmtree(session.temp_dir, ignore_errors=True)
        await session.delete()
        raise HTTPException(status_code=410, detail="Upload session has expired")
    
    # Check if all chunks are received
    if not session.is_complete():
        missing_chunks = set(range(session.total_chunks)) - set(session.chunks_received)
        raise HTTPException(
            status_code=400, 
            detail=f"Missing chunks: {sorted(missing_chunks)}"
        )
    
    # Combine chunks into final file
    final_file_path = await FileService.combine_chunks(
        session.temp_dir, 
        session.total_chunks, 
        session.filename
    )
    
    # Create file info
    file_info = {
        "original_name": session.filename,
        "name": os.path.basename(final_file_path),
        "file_path": final_file_path,
        "file_size": session.file_size,
        "mime_type": session.mime_type or "application/octet-stream"
    }
    
    # Analyze file for georeferencing
    analysis = analyze_raster_file(file_info["file_path"])
    is_georeferenced = analysis.get("is_georeferenced", False)
    
    # Create file object
    if is_georeferenced:
        file_obj = await models_factory.create_geo_file(
            file_info, session.tags, parent_path=session.parent_path)
    else:
        file_obj = await models_factory.create_file(
            file_info, session.tags, parent_path=session.parent_path)
    
    file_obj.owner_user_id = current_user.id
    file_obj.permissions = 0o644
    await file_obj.save()
    
    # Clean up temp directory and session
    shutil.rmtree(session.temp_dir, ignore_errors=True)
    await session.delete()
    
    return TreeItemResponse.model_validate(file_obj)


@router.post("/tree-items/{item_id}/probe")
async def probe_tree_item(item_id: uuid.UUID, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Probe a tree item to check if it can be georeferenced with GDAL"""
    tree_item = await TreeItem.get_or_none(id=item_id)
    if not tree_item:
        raise HTTPException(status_code=404, detail="TreeItem not found")

    await require_permission(tree_item, current_user, Permission.READ)

    # Only files can be georeferenced
    if not tree_item.is_file:
        return {
            "can_georeference": False,
            "gdal_compatible": False,
            "error": "Only files can be georeferenced"
        }
    
    file_obj = await tree_item.get_object()
    file_path = file_obj.file_path
    
    # Analyze the raster file
    analysis = analyze_raster_file(file_path)
    
    if not analysis.get("gdal_compatible", False):
        return {
            "can_georeference": False,
            "gdal_compatible": False,
            "error": analysis.get("error", "File cannot be opened by GDAL")
        }
    
    return {
        "can_georeference": True,
        "gdal_compatible": True,
        "is_already_georeferenced": analysis.get("is_georeferenced", False),
        "image_info": {
            "width": analysis.get("width"),
            "height": analysis.get("height"),
            "bands": analysis.get("bands"),
            "has_projection": analysis.get("has_projection", False),
            "has_geotransform": analysis.get("has_geotransform", False)
        }
    }
    return result


@router.post("/tree-items/{item_id}/convert-to-geo-raster", response_model=TreeItemResponse)
async def convert_to_geo_raster(item_id: uuid.UUID, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Convert a RawFile to GeoRasterFile for georeferencing"""
    tree_item = await TreeItem.get_or_none(id=item_id)
    if not tree_item:
        raise HTTPException(status_code=404, detail="TreeItem not found")

    await require_permission(tree_item, current_user, Permission.WRITE)

    raw_file = await tree_item.get_object()
    if not raw_file:
        raise HTTPException(status_code=404, detail="Raw file not found")

    geo_raster_file_obj = await models_factory.convert_to_geo_raster(raw_file, "uploads")
    
    # Ensure the new geo raster file is marked as not georeferenced initially
    geo_raster_file_obj.is_georeferenced = False
    await geo_raster_file_obj.save()

    # Update TreeItem to point to GeoRasterFile
    tree_item.object_type = "geo_raster_file"
    tree_item.object_id = geo_raster_file_obj.id
    await tree_item.save()

    return TreeItemResponse.model_validate(tree_item)


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: uuid.UUID, 
    current_user: Optional[User] = Depends(get_current_user_optional)):
    """Download a file"""
    tree_item = await TreeItem.get_or_none(id=file_id)
    if not tree_item:
        raise HTTPException(status_code=404, detail="TreeItem not found")

    await require_permission(tree_item, current_user, Permission.READ)
    
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
        media_type=obj.mime_type,
        headers={"Content-Disposition": f"inline"}
    )


# MapServer endpoints (specialized for geospatial files)
@router.get("/files/{file_id}/map")
async def get_file_map(file_id: uuid.UUID):
    """Get a MapServer URL for a GeoTIFF file"""
    file_obj = await FileService.get_file(str(file_id))
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if this is a geo raster file
    if file_obj.object_type != "geo_raster_file":
        raise HTTPException(status_code=400, detail="File type not supported for mapping")
    
    # Get the actual geo raster file object
    geo_raster_file = await file_obj.get_object()
    
    # Use stored config path
    if not geo_raster_file.map_config_path:
        raise HTTPException(status_code=400, detail="No map configuration available")
    
    map_url = mapserver_service.get_map_url_from_config(geo_raster_file.map_config_path)
    if not map_url:
        raise HTTPException(status_code=400, detail="Failed to generate map URL")
    
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
    
    extent = mapserver_service.get_file_extent(file_path)
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
            georeference.ControlPoint(cp.image_x, cp.image_y, cp.world_x, cp.world_y)
            for cp in request.control_points
        ]
        
        # Validate control points
        validation_results = georeference.validate_control_points(control_points)
        
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
        georeference.ControlPoint(cp.image_x, cp.image_y, cp.world_x, cp.world_y)
        for cp in request.control_points
    ]
    
    # Validate control points
    validation_results = georeference.validate_control_points(control_points)
    
    if not validation_results['valid']:
        raise HTTPException(status_code=400, detail=f"Invalid control points: {validation_results['errors']}")
    
    # Create the final georeferenced file
    georeferenced_path = georeference.warp_image_with_control_points(
        file_path,
        control_points,
        request.control_points_srs
    )
    
    # save old file path
    old_file_path = file_path

    # regenerate map config to clear cache on mapserver
    map_config_path = mapserver_service._create_map_config(georeferenced_path)
    geo_raster_file.map_config_path = map_config_path
    geo_raster_file.file_path = georeferenced_path
    geo_raster_file.is_georeferenced = True
    
    await geo_raster_file.save()

    if os.path.exists(old_file_path) and old_file_path != geo_raster_file.original_file_path:
        os.remove(old_file_path)
    
    
    return {
        "message": "Georeferencing applied successfully",
        "file": TreeItemResponse.model_validate(tree_obj),
        "validation_results": validation_results
    }


@router.post("/files/{file_id}/reset-georeferencing")
async def reset_georeferencing(file_id: uuid.UUID, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Reset georeferencing by removing warped file and restoring original file path"""
    tree_obj = await models.TreeItem.get_or_none(id=file_id, object_type="geo_raster_file")
    if not tree_obj:
        raise HTTPException(status_code=404, detail="Geo raster file not found")
    
    await require_permission(tree_obj, current_user, Permission.WRITE)
    
    geo_raster_file = await tree_obj.get_object()
    old_file_path = geo_raster_file.file_path
    
    # Check if there's an original file path to restore
    if not geo_raster_file.original_file_path:
        raise HTTPException(status_code=400, detail="No original file path available to restore")
    
    # Check if original file still exists
    if not os.path.exists(geo_raster_file.original_file_path):
        raise HTTPException(status_code=404, detail="Original file not found on disk")

    if (geo_raster_file.file_path == geo_raster_file.original_file_path):
        raise HTTPException(status_code=400, detail="File is already in original state")

    # copy original file to file path and generate new uuid name with same extension
    new_file_path = Path(geo_raster_file.original_file_path).parent / f"{uuid.uuid4()}.tif"
    print(f"Copying original file to {new_file_path}")
    shutil.copy(geo_raster_file.original_file_path, str(new_file_path))

    # regenerate map config to clear cache on mapserver
    old_map_config_path = geo_raster_file.map_config_path
    map_config_path = mapserver_service._create_map_config(new_file_path)
    geo_raster_file.map_config_path = map_config_path
    geo_raster_file.file_path = new_file_path
    geo_raster_file.is_georeferenced = False  # Mark as not georeferenced

    await geo_raster_file.save()
    
    # Clear the map config since the file is no longer georeferenced
    if old_map_config_path and os.path.exists(old_map_config_path):
        os.remove(old_map_config_path)
    
    # Remove the previous warped file if it exists
    if os.path.exists(old_file_path):
        os.remove(old_file_path)
    
    return {
        "message": "Georeferencing reset successfully",
        "file": TreeItemResponse.model_validate(tree_obj)
    }
    
