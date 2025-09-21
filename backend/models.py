from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
import hashlib
import secrets
import os

from datetime import datetime
from typing import Dict, Any, Optional, Union


class LTreeField(fields.Field):
    SQL_TYPE = "LTREE"
    field_type = str


class User(models.Model):
    """User model for authentication and permissions"""
    id = fields.UUIDField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=128)  # SHA-512 hash
    salt = fields.CharField(max_length=32)  # Random salt for password hashing
    is_active = fields.BooleanField(default=True)
    is_admin = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "users"

    def __str__(self):
        return f"User(id={self.id}, username='{self.username}')"
    
    def set_password(self, password: str):
        """Hash and set password with salt"""
        self.salt = secrets.token_hex(16)
        self.password_hash = hashlib.sha512((password + self.salt).encode()).hexdigest()
    
    def check_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        return self.password_hash == hashlib.sha512((password + self.salt).encode()).hexdigest()


class Group(models.Model):
    """Group model for organizing users and permissions"""
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # Many-to-many relationship with users
    members = fields.ManyToManyField('models.User', related_name='groups', through='user_groups')
    
    class Meta:
        table = "groups"

    def __str__(self):
        return f"Group(id={self.id}, name='{self.name}')"

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
    
    def get_download_path(self) -> str:
        """Get the path for downloading this file"""
        return self.file_path


class GeoRasterFile(models.Model):
    """Model for georeferenced raster files (GeoTIFF, georeferenced images)
    """
    id = fields.UUIDField(pk=True)
    original_name = fields.CharField(max_length=500)
    file_path = fields.CharField(max_length=1000)  # Current file path (may be georeferenced version)
    original_file_path = fields.CharField(max_length=1000, null=True)  # Original before georeferencing
    map_config_path = fields.CharField(max_length=1000, null=True)  # MapServer config file path
    is_georeferenced = fields.BooleanField(default=False)  # Whether the file has been properly georeferenced
    file_size = fields.BigIntField()
    mime_type = fields.CharField(max_length=200)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "geo_raster_files"

    def __str__(self):
        return f"GeoRasterFile(id={self.id}, name='{self.original_name}')"
    
    def get_download_path(self) -> str:
        """Get the path for downloading this file
        
        Use original file path for downloads if available, otherwise use main file path
        """
        if self.original_file_path:
            return self.original_file_path
        return self.file_path


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
    # "raw_file", "geo_raster_file", "collection"
    object_type = fields.CharField(max_length=50)
    object_id = fields.UUIDField()
    
    # User-editable metadata (safe to modify)
    tags = fields.JSONField(default=dict)
    
    # Hierarchical path using LTREE
    path = LTreeField(default="root")
    
    # Linux-style permissions
    owner_user = fields.ForeignKeyField('models.User', related_name='owned_items', null=True)
    owner_group = fields.ForeignKeyField('models.Group', related_name='owned_items', null=True)
    permissions = fields.IntField(default=0o644)  # rwxrwxrwx format, but only rw- rw- r-- used
    
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
    
    # Permission checking methods
    async def can_read(self, user: Optional['User'] = None) -> bool:
        """Check if user has read permission on this item"""
        if user is None:
            # No user provided, check "other" permissions (last 3 bits)
            return bool(self.permissions & 0o004)
        
        if user.is_admin:
            return True
        
        # Check owner permissions (first 3 bits)
        if self.owner_user_id == user.id:
            return bool(self.permissions & 0o400)
        
        # Check group permissions (middle 3 bits)
        if self.owner_group_id:
            user_groups = await user.groups.all()
            if any(group.id == self.owner_group_id for group in user_groups):
                return bool(self.permissions & 0o040)
        
        # Check other permissions (last 3 bits)
        return bool(self.permissions & 0o004)
    
    async def can_write(self, user: Optional['User'] = None) -> bool:
        """Check if user has write permission on this item"""
        if user is None:
            # No user provided, check "other" permissions
            return bool(self.permissions & 0o002)
        
        if user.is_admin:
            return True
        
        # Check owner permissions
        if self.owner_user_id == user.id:
            return bool(self.permissions & 0o200)
        
        # Check group permissions
        if self.owner_group_id:
            user_groups = await user.groups.all()
            if any(group.id == self.owner_group_id for group in user_groups):
                return bool(self.permissions & 0o020)
        
        # Check other permissions
        return bool(self.permissions & 0o002)
    
    def get_permission_string(self) -> str:
        """Get human-readable permission string like 'rw-rw-r--'"""
        perm = self.permissions
        result = ""
        
        # Owner permissions
        result += "r" if perm & 0o400 else "-"
        result += "w" if perm & 0o200 else "-"
        result += "-"  # Execute not used
        
        # Group permissions  
        result += "r" if perm & 0o040 else "-"
        result += "w" if perm & 0o020 else "-"
        result += "-"  # Execute not used
        
        # Other permissions
        result += "r" if perm & 0o004 else "-"
        result += "w" if perm & 0o002 else "-"
        result += "-"  # Execute not used
        
        return result



# Pydantic models for API
User_Pydantic = pydantic_model_creator(User, name="User", exclude=("password_hash", "salt"))
Group_Pydantic = pydantic_model_creator(Group, name="Group")
TreeItem_Pydantic = pydantic_model_creator(TreeItem, name="TreeItem")
RawFile_Pydantic = pydantic_model_creator(RawFile, name="RawFile")
GeoRasterFile_Pydantic = pydantic_model_creator(GeoRasterFile, name="GeoRasterFile")
Collection_Pydantic = pydantic_model_creator(Collection, name="Collection")

# Backward compatibility aliases
File = TreeItem
File_Pydantic = TreeItem_Pydantic

KnownTreeItemTypes = RawFile_Pydantic | GeoRasterFile_Pydantic | Collection_Pydantic
