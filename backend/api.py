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



@router.get("/files/{file_id}/map")
async def get_file_map(file_id: uuid.UUID):
    """Get a MapServer URL for a GeoTIFF file"""
    file_obj = await FileService.get_file(file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    map_url = mapserver_service.get_map_url(file_obj.name)
    if not map_url:
        raise HTTPException(status_code=400, detail="File type not supported for mapping")
    
    return {"map_url": map_url}


@router.get("/files/{file_id}/extent")
async def get_file_extent(file_id: uuid.UUID):
    """Get the extent (bounding box) of a GeoTIFF file"""
    file_obj = await FileService.get_file(file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    extent = mapserver_service.get_file_extent(file_obj.name)
    if not extent:
        raise HTTPException(status_code=400, detail="File type not supported for extent calculation")
    
    return {"extent": extent}

# MapServer endpoints
@router.get("/files/{file_id}/preview")
async def get_file_preview(file_id: uuid.UUID):
    """Get a preview URL for a file (especially GeoTIFF)"""
    file_obj = await FileService.get_file(file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    preview_url = mapserver_service.get_preview_url(file_obj.name)
    if not preview_url:
        raise HTTPException(status_code=400, detail="File type not supported for preview")
    
    return {"preview_url": preview_url}


@router.get("/{commit_id}/objects", response_model=ObjectsListResponse)
async def list_tree_root(commit_id: str):
    return await list_tree(commit_id, path=None)


@router.get("/{commit_id}/{path:path}/objects", response_model=ObjectsListResponse)
async def list_tree_by_path(commit_id: str, path: str):
    return await list_tree(commit_id, path)


async def list_tree(commit_id: str, path: str | None = None):
    commit = await models.Commit.get_or_none(id=commit_id)

    resolved_path = await git_service.resolve_tree(await commit.tree, path or '')
    tree = resolved_path[-1][0]

    entries_query = models.TreeEntry.filter(id__in=tree.entries)
    entries = await entries_query.all()

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
        skip=0,
        limit=0
    )


@router.get("/{commit_id}/{path:path}", response_model=TreeEntryResponse)
async def get_tree_object(commit_id: str, path: str):
    commit = await models.Commit.get_or_none(id=commit_id)

    entry = await git_service.resolve_entry(await commit.tree, path or '')

    if entry.object_type == 'file':
        object = await models.File.filter(id=entry.object_id).get()
    else:
        object = await models.Tree.filter(id=entry.object_id).get()
        
    entry.object = object

    return entry


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
    path: Optional[str] = Body(...),
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
        await index.insert_tree_entry(new_entry, path)
        await index.commit(f"Add file {object.name}", ref)

    return TreeEntryResponse(
        id=new_entry.id,
        object_type=obj_type,
        object=object,
        path=tree_entry_path
    )


@router.put("/{commit_id}/{path:path}", response_model=TreeEntryResponse)
async def update_object_in_tree(
    commit_id: str = Path(..., description="Commit ID"),
    path: str = Path(..., description="TreeEntry (object) path"),
    request: FileUpdateRequest = None
):
    """Update a file object in a tree (by tree entry). Only file objects are supported for now."""
    ref = await models.Ref.get_or_none(name="main")

    # Find the commit
    commit = await models.Commit.get_or_none(id=commit_id)
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")


    entry = await git_service.resolve_entry(await commit.tree, path)
    if not entry:
        raise HTTPException(status_code=404, detail="Tree entry not found")

    # TODO: add support for other object types
    if entry.object_type != 'file':
        raise HTTPException(status_code=400, detail="Only file objects can be updated at this time")
    
    orig_file_obj = await models.File.get_or_none(id=entry.object_id)
    if not orig_file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    
    print('Requested tags: ', request.tags)
        
    # Copy file record, assign new tags
    new_file_obj = await models.File.create(   
        name=orig_file_obj.name,
        original_name=orig_file_obj.original_name,
        file_path=orig_file_obj.file_path,
        file_size=orig_file_obj.file_size,
        mime_type=orig_file_obj.mime_type,
        base_file_type=orig_file_obj.base_file_type,
        tags = request.tags,
    )
    # todo: do I need this?
    new_file_obj.sha1 = models.calculate_file_obj_hash(new_file_obj)
    await new_file_obj.save()

    async with git_service.stage_changes(head=commit) as index:
        new_entry = await models.TreeEntry.create(
            path=entry.path,
            object_type='file',
            object_id=new_file_obj.id
        )
        await index.remove_tree_entry(path)


        match path.rsplit('/', 1):
            case folder, _:
                await index.insert_tree_entry(new_entry, folder)
            case _:
                await index.insert_tree_entry(new_entry, None)
        
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