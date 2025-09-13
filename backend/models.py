from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

from datetime import datetime
from typing import Dict, Any, Optional, Union


class LTreeField(fields.Field):
    SQL_TYPE = "LTREE"
    field_type = str


# Specialized Models for Different Content Types

class RawFile(models.Model):
    """Model for raw files (documents, non-geospatial images, etc.)
    
    Note: Metadata like sha1 is stored in TreeItem.tags
    """
    id = fields.UUIDField(pk=True)
    original_name = fields.CharField(max_length=500)
    file_path = fields.CharField(max_length=1000)
    file_size = fields.BigIntField()
    mime_type = fields.CharField(max_length=200)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "raw_files"

    def __str__(self):
        return f"RawFile(id={self.id}, name='{self.original_name}', size={self.file_size})"


class GeoRasterFile(models.Model):
    """Model for georeferenced raster files (GeoTIFF, georeferenced images)
    
    Note: Metadata like sha1, is_georeferenced, georeferencing_method, target_srs,
    control_points_count, and georeferencing_accuracy are stored in TreeItem.tags
    """
    id = fields.UUIDField(pk=True)
    original_name = fields.CharField(max_length=500)
    file_path = fields.CharField(max_length=1000)  # Current file path (may be georeferenced version)
    original_file_path = fields.CharField(max_length=1000, null=True)  # Original before georeferencing
    file_size = fields.BigIntField()
    mime_type = fields.CharField(max_length=200)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "geo_raster_files"

    def __str__(self):
        return f"GeoRasterFile(id={self.id}, name='{self.original_name}')"


class Collection(models.Model):
    """Model for collections/folders - name and description are stored in TreeItem.tags"""
    id = fields.UUIDField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "collections"

    def __str__(self):
        return f"Collection(id={self.id})"


class TreeItem(models.Model):
    """Base navigation/hierarchy model with polymorphic relationship to specialized models"""
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)
    
    # Polymorphic relationship
    object_type = fields.CharField(max_length=50)  # "raw_file", "geo_raster_file", "collection"
    object_id = fields.UUIDField()
    
    # User-editable metadata (safe to modify)
    tags = fields.JSONField(default=dict)
    
    # Hierarchical path using LTREE
    path = LTreeField(default="root")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "tree_items"
        indexes = [
            ("object_type", "object_id"),
        ]

    def __str__(self):
        return f"TreeItem(id={self.id}, name='{self.name}', type='{self.object_type}', path='{self.path}')"
    
    @property
    def type(self) -> str:
        """Backward compatibility property"""
        if self.object_type in ["raw_file", "geo_raster_file"]:
            return "file"
        elif self.object_type == "collection":
            return "collection"
        return "unknown"
    
    @property
    def is_file(self) -> bool:
        """Check if this tree item is a file"""
        return self.object_type in ["raw_file", "geo_raster_file"]
    
    @property
    def is_collection(self) -> bool:
        """Check if this tree item is a collection"""
        return self.object_type == "collection"
    
    async def get_object(self) -> Union[RawFile, GeoRasterFile, Collection]:
        """Get the actual object this tree item points to"""
        if self.object_type == "raw_file":
            return await RawFile.get(id=self.object_id)
        elif self.object_type == "geo_raster_file":
            return await GeoRasterFile.get(id=self.object_id)
        elif self.object_type == "collection":
            return await Collection.get(id=self.object_id)
        else:
            raise ValueError(f"Unknown object_type: {self.object_type}")
    
    # Convenience properties for accessing object data (for backward compatibility)
    @property
    async def object(self) -> Union[RawFile, GeoRasterFile, Collection]:
        """Async property to get the object"""
        return await self.get_object()
    
    async def get_file_path(self) -> str:
        """Get file path from related object"""
        obj = await self.get_object()
        if hasattr(obj, 'file_path'):
            return obj.file_path
        return ""
    
    async def get_base_file_type(self) -> str:
        """Get base file type based on object type"""
        if self.object_type == "raw_file":
            return "raw"
        elif self.object_type == "geo_raster_file":
            return "raster"
        elif self.object_type == "collection":
            return "collection"
        return "raw"
    


# Pydantic models for API
TreeItem_Pydantic = pydantic_model_creator(TreeItem, name="TreeItem")
RawFile_Pydantic = pydantic_model_creator(RawFile, name="RawFile")
GeoRasterFile_Pydantic = pydantic_model_creator(GeoRasterFile, name="GeoRasterFile")
Collection_Pydantic = pydantic_model_creator(Collection, name="Collection")

# Backward compatibility aliases
File = TreeItem
File_Pydantic = TreeItem_Pydantic

KnownTreeItemTypes = RawFile_Pydantic | GeoRasterFile_Pydantic | Collection_Pydantic
