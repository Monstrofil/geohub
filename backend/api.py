from fastapi import APIRouter, UploadFile, File, Form, Body, HTTPException, Depends, Path
from fastapi.responses import FileResponse as FastAPIFileResponse
from typing import List, Dict, Optional, ForwardRef
import os
import datetime 
import json
import uuid
import git_service
import hashlib
import random
from pydantic import BaseModel, ConfigDict

import models
from services import FileService, FileTypeService, CollectionsService
from mapserver_service import MapServerService


router = APIRouter(tags=["files"])

# Initialize MapServer service
mapserver_service = MapServerService()


# Pydantic models for request/response
class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    sha1: str | None
    original_name: str
    file_size: int
    mime_type: str
    base_file_type: str
    tags: Dict[str, str]
    created_at: datetime.datetime
    updated_at: datetime.datetime


class FileListResponse(BaseModel):
    files: list[FileResponse]
    total: int
    skip: int
    limit: int


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    name: str
    tags: Dict[str, str]


class TreeEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    object_type: str
    object: FileResponse | CategoryResponse

    path: str


class ObjectsListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    objects: list[TreeEntryResponse]
    total: int
    skip: int
    limit: int


class FileUpdateRequest(BaseModel):
    tags: Dict[str, str]


class FileSearchRequest(BaseModel):
    tags: Dict[str, str]
    base_type: Optional[str] = None
    skip: int = 0
    limit: int = 100


class RefResponse(BaseModel):
    name: str
    commit_id: uuid.UUID


class CommitResponse(BaseModel):
    id: str
    tree_id: str
    parent_id: Optional[str]
    message: str
    timestamp: str


# class TreeEntryResponse(BaseModel):
#     id: int
#     path: str
#     object_type: str
#     object_id: int


class TreeResponse(BaseModel):
    id: str
    entries: list[TreeEntryResponse]


@router.get("/{commit_id}/objects", response_model=ObjectsListResponse)
async def list_tree(commit_id: str, skip: int = 0, limit: int = 100):
    commit = await models.Commit.get_or_none(id=commit_id)
    tree = await commit.tree

    entries = await models.TreeEntry.filter(id__in=tree.entries).offset(skip).limit(limit)

    # Separate IDs by type
    file_ids = [entry.object_id for entry in entries if entry.object_type == 'file']
    tree_ids = [entry.object_id for entry in entries if entry.object_type == 'tree']

    files = await models.File.filter(id__in=file_ids)
    trees = await models.Tree.filter(id__in=tree_ids)

    files_mapping = {f.id: f for f in files}
    trees_mapping = {t.id: t for t in trees}

    # Attach the correct object to each entry
    for entry in entries:
        if entry.object_type == 'file':
            object = files_mapping.get(entry.object_id)
        elif entry.object_type == 'tree':
            object = trees_mapping.get(entry.object_id)
        
        entry.object = object

    return ObjectsListResponse(
        objects=entries,
        total=len(entries),
        skip=skip,
        limit=limit
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


@router.put("/files/{file_id}", response_model=FileResponse)
async def update_file(file_id: int, request: FileUpdateRequest):
    """Update file tags (and in the future, other fields)"""
    file_obj = await models.File.get_or_none(id=file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    # Update tags
    new_file_id = await FileService.update_file_tags(file_id, tags=request.tags)

    file_obj = await models.File.get_or_none(id=new_file_id)
    if not file_obj:
        raise HTTPException(status_code=500, detail="Updated file not found")

    # Return the updated file as a dict with ISO-formatted datetimes
    return {
        "id": file_obj.id,
        "name": file_obj.name,
        "sha1": file_obj.sha1,
        "original_name": file_obj.original_name,
        "file_size": file_obj.file_size,
        "mime_type": file_obj.mime_type,
        "base_file_type": file_obj.base_file_type,
        "tags": file_obj.tags,
        "created_at": file_obj.created_at.isoformat(),
        "updated_at": file_obj.updated_at.isoformat(),
    }


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


@router.get("/refs", response_model=List[RefResponse])
async def list_refs():
    refs = await models.Ref.all().prefetch_related("commit")
    return [
        RefResponse(name=ref.name, commit_id=ref.commit_id)
        for ref in refs
    ]


@router.get("/commits", response_model=List[CommitResponse])
async def list_commits():
    commits = await models.Commit.all().prefetch_related("tree", "parent")
    return [
        CommitResponse(
            id=commit.id,
            tree_id=commit.tree_id,
            parent_id=commit.parent_id,
            message=commit.message,
            timestamp=commit.timestamp.isoformat(),
        ) for commit in commits
    ]


@router.get("/commits/{commit_id}", response_model=CommitResponse)
async def get_commit(commit_id: str):
    commit = await models.Commit.get_or_none(id=commit_id)
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")
    return CommitResponse(
        id=commit.id,
        tree_id=commit.tree_id,
        parent_id=commit.parent_id,
        message=commit.message,
        timestamp=commit.timestamp.isoformat(),
    )


@router.get("/trees/{tree_id}", response_model=TreeResponse)
async def get_tree(tree_id: str):
    tree = await models.Tree.get_or_none(id=tree_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Tree not found")
    
    entries = await models.TreeEntry.filter(sha1__in=tree.entries)
    return TreeResponse(
        id=tree.id,
        entries=[
            TreeEntryResponse(
                id=entry.id,
                sha1=entry.sha1,
                object_type=entry.object_type,
                object_id=entry.object_id
            ) for entry in entries
        ]
    )

@router.post("/{commit_id}/objects", response_model=TreeEntryResponse)
async def add_object_in_tree(
    commit_id: str = Path(..., description="Commit ID"),
    file: UploadFile | None = None,
    name: Optional[str] = Body(...),
    tags: Optional[str] = Form(None)
):
    """Add a new file object to a tree (by commit)."""
    ref = await models.Ref.get_or_none(name="main")

    commit = await models.Commit.get_or_none(id=commit_id)
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")

    object_tags = {}
    if tags:
        try:
            object_tags = json.loads(tags)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid tags format")


    if file is not None:
        object, obj_type = await FileService.create_file(file, object_tags), "file"
    else:
        object, obj_type = await CollectionsService.create_collection(name, object_tags), "tree"

    tree_entry_path = hashlib.sha1(str(random.getrandbits(256)).encode()).hexdigest()
    async with git_service.stage_changes(head=commit) as index:
        new_entry = await models.TreeEntry.create(
            path=tree_entry_path,
            object_type=obj_type,
            object_id=object.id
        )
        await index.add_tree_entry(new_entry)
        await index.commit(f"Add file {object.name}", ref)

    return TreeEntryResponse(
        id=new_entry.id,
        object_type=obj_type,
        object=object,
        path=tree_entry_path
    )


@router.put("/{commit_id}/objects/{tree_entry_id}", response_model=TreeEntryResponse)
async def update_object_in_tree(
    commit_id: str = Path(..., description="Commit ID"),
    tree_entry_id: str = Path(..., description="TreeEntry (object) ID"),
    request: FileUpdateRequest = None
):
    """Update a file object in a tree (by tree entry). Only file objects are supported for now."""
    ref = await models.Ref.get_or_none(name="main")

    # Find the commit
    commit = await models.Commit.get_or_none(id=commit_id)
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")


    entry = await models.TreeEntry.get_or_none(id=tree_entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Tree entry not found")

    # TODO: add support for other object types
    if entry.object_type != 'file':
        raise HTTPException(status_code=400, detail="Only file objects can be updated at this time")
    
    orig_file_obj = await models.File.get_or_none(id=entry.object_id)
    if not orig_file_obj:
        raise HTTPException(status_code=404, detail="File not found")
        
    # Copy file record, assign new tags
    new_file_obj = orig_file_obj
    new_file_obj.id = None
    new_file_obj.tags = request.tags
    new_file_obj.sha1 = models.calculate_file_obj_hash(new_file_obj)
    await new_file_obj.save()

    async with git_service.stage_changes(head=commit) as index:
        new_entry = await git_service.create_tree_entry(
            entry.object_type, new_file_obj.id, entry.path)
        await index.update_tree_entry(entry, new_entry)

        await index.commit("Update file %s", ref)

    file_obj = await models.File.get_or_none(id=new_file_obj.id)
    if not file_obj:
        raise HTTPException(status_code=500, detail="Updated file not found")

    return TreeEntryResponse(
        id=entry.id,
        object_type=entry.object_type,
        object=file_obj,
        path=entry.path
    ) 