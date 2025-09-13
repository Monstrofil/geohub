"""
Helper functions for working with the new model architecture
"""

from typing import Union, Dict, Any, Optional
import uuid
from pathlib import Path

from models import TreeItem, RawFile, GeoRasterFile, Collection


class ModelFactory:
    """Factory for creating TreeItems with appropriate specialized models"""
    
    @staticmethod
    async def create_raw_file(
        name: str,
        file_path: str,
        original_name: str,
        file_size: int,
        mime_type: str,
        parent_path: str = "root",
        tags: Optional[Dict[str, Any]] = None
    ) -> TreeItem:
        """Create a TreeItem with RawFile"""
        
        # Create RawFile (minimal model)
        raw_file = await RawFile.create(
            original_name=original_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type
        )
        
        # Prepare tags with base file type
        file_tags = tags or {}
        file_tags.update({
            "base_file_type": "raw"
        })
        
        # Create TreeItem
        tree_item = await TreeItem.create(
            name=name,
            object_type="raw_file",
            object_id=raw_file.id,
            path=parent_path,
            tags=file_tags
        )
        
        return tree_item
    
    @staticmethod
    async def create_geo_raster_file(
        name: str,
        file_path: str,
        original_name: str,
        file_size: int,
        mime_type: str,
        parent_path: str = "root",
        tags: Optional[Dict[str, Any]] = None,
        original_file_path: Optional[str] = None
    ) -> TreeItem:
        """Create a TreeItem with GeoRasterFile"""
        
        # Create GeoRasterFile (minimal model)
        geo_raster = await GeoRasterFile.create(
            original_name=original_name,
            file_path=file_path,
            original_file_path=original_file_path,
            file_size=file_size,
            mime_type=mime_type
        )
        
        # Prepare tags with base file type  
        file_tags = tags or {}
        file_tags.update({
            "base_file_type": "raster"
        })
        
        # Create TreeItem
        tree_item = await TreeItem.create(
            name=name,
            object_type="geo_raster_file",
            object_id=geo_raster.id,
            path=parent_path,
            tags=file_tags
        )
        
        return tree_item
    
    @staticmethod
    async def create_collection(
        name: str,
        parent_path: str = "root",
        description: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> TreeItem:
        """Create a TreeItem with Collection"""
        
        # Create Collection (minimal model - data stored in TreeItem.tags)
        collection = await Collection.create()
        
        # Prepare tags with name and description
        collection_tags = tags or {}
        if description:
            collection_tags["description"] = description
        
        # Create TreeItem
        tree_item = await TreeItem.create(
            name=name,
            object_type="collection",
            object_id=collection.id,
            path=parent_path,
            tags=collection_tags
        )
        
        return tree_item


class TreeItemService:
    """Service for working with TreeItems and their related objects"""
    
    @staticmethod
    async def get_tree_item_with_object(tree_item_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Get TreeItem with its related object data"""
        tree_item = await TreeItem.get(id=tree_item_id)
        obj = await tree_item.get_object()
        
        # Build unified response
        result = {
            'id': tree_item.id,
            'name': tree_item.name,
            'object_type': tree_item.object_type,
            'tags': tree_item.tags,
            'path': tree_item.path,
            'created_at': tree_item.created_at,
            'updated_at': tree_item.updated_at,
            
            # Object-specific data
            'object': {},
        }
        
        if isinstance(obj, RawFile):
            result['object'] = {
                'original_name': obj.original_name,
                'file_path': obj.file_path,
                'file_size': obj.file_size,
                'mime_type': obj.mime_type,
                # Note: sha1 and base_file_type are now in TreeItem.tags
            }
        elif isinstance(obj, GeoRasterFile):
            result['object'] = {
                'original_name': obj.original_name,
                'file_path': obj.file_path,
                'original_file_path': obj.original_file_path,
                'file_size': obj.file_size,
                'mime_type': obj.mime_type,
                'image_width': obj.image_width,
                'image_height': obj.image_height,
                'image_bands': obj.image_bands,
                # Note: sha1, georeferencing metadata are now in TreeItem.tags
            }
        elif isinstance(obj, Collection):
            result['object'] = {
                # Collection is minimal - name and description are in TreeItem.tags
                'type': 'collection'
            }
        
        return result
    
    @staticmethod
    async def update_georeferencing(
        tree_item_id: Union[str, uuid.UUID],
        new_file_path: Optional[str] = None
    ) -> None:
        """Update georeferencing information for a GeoRasterFile"""
        tree_item = await TreeItem.get(id=tree_item_id)
        
        if tree_item.object_type != "geo_raster_file":
            raise ValueError("Can only update georeferencing for geo_raster_file objects")
        
        geo_raster = await GeoRasterFile.get(id=tree_item.object_id)
        
        # Update file path if provided (e.g., after georeferencing creates new file)
        if new_file_path is not None:
            if geo_raster.original_file_path is None:
                geo_raster.original_file_path = geo_raster.file_path
            geo_raster.file_path = new_file_path
            await geo_raster.save()
    
    @staticmethod
    async def get_files_by_type(object_type: str, limit: int = 100, offset: int = 0):
        """Get TreeItems by object type"""
        return await TreeItem.filter(object_type=object_type).limit(limit).offset(offset)
    
    @staticmethod
    async def get_tree_items_in_path(path: str, limit: int = 100, offset: int = 0):
        """Get TreeItems in a specific path"""
        return await TreeItem.filter(path__startswith=path).limit(limit).offset(offset)


# Backward compatibility functions
async def get_file_by_id(file_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
    """Get file by ID with backward compatibility"""
    return await TreeItemService.get_tree_item_with_object(file_id)

async def create_file(file_data: Dict[str, Any]) -> TreeItem:
    """Create file with backward compatibility"""
    base_file_type = file_data.get('base_file_type', 'raw')
    
    if base_file_type == 'raster':
        return await ModelFactory.create_geo_raster_file(
            name=file_data['name'],
            file_path=file_data['file_path'],
            original_name=file_data.get('original_name', file_data['name']),
            file_size=file_data.get('file_size', 0),
            mime_type=file_data.get('mime_type', ''),
            parent_path=file_data.get('parent_path', 'root'),
            tags=file_data.get('tags', {})
        )
    else:
        return await ModelFactory.create_raw_file(
            name=file_data['name'],
            file_path=file_data['file_path'],
            original_name=file_data.get('original_name', file_data['name']),
            file_size=file_data.get('file_size', 0),
            mime_type=file_data.get('mime_type', ''),
            parent_path=file_data.get('parent_path', 'root'),
            tags=file_data.get('tags', {})
        )
