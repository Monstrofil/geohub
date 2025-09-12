from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

import hashlib
from pathlib import Path

from typing import Dict, Any
import json


class LTreeField(fields.Field):
    SQL_TYPE = "LTREE"
    field_type = str


class TreeItem(models.Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)
    type = fields.CharField(max_length=20)  # "file" or "collection"
    tags = fields.JSONField(default=dict)  # All attributes go here now
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # Hierarchical path using LTREE
    path = LTreeField(default="root")

    class Meta:
        table = "tree_items"

    def __str__(self):
        return f"TreeItem(id={self.id}, name='{self.name}', type='{self.type}', path='{self.path}')"
    
    @property
    def is_file(self) -> bool:
        """Check if this tree item is a file"""
        return self.type == "file"
    
    @property
    def is_collection(self) -> bool:
        """Check if this tree item is a collection"""
        return self.type == "collection"
    
    # File-specific properties (access tags)
    @property
    def original_name(self) -> str:
        """Get original filename from tags"""
        return self.tags.get("original_name", self.name)
    
    @property
    def file_path(self) -> str:
        """Get file path from tags"""
        return self.tags.get("file_path", "")
    
    @property
    def file_size(self) -> int:
        """Get file size from tags"""
        return self.tags.get("file_size", 0)
    
    @property
    def mime_type(self) -> str:
        """Get MIME type from tags"""
        return self.tags.get("mime_type", "")
    
    @property
    def base_file_type(self) -> str:
        """Get base file type from tags"""
        return self.tags.get("base_file_type", "raw")
    
    @property
    def sha1(self) -> str:
        """Get SHA1 hash from tags"""
        return self.tags.get("sha1", "")


def calculate_tree_item_hash(tree_item: TreeItem):
    """Calculate hash for a file tree item"""
    if not tree_item.is_file:
        return None
        
    file_path = tree_item.file_path
    if not file_path or not Path(file_path).exists():
        return None
        
    content = Path(file_path).read_bytes()
    tags = tree_item.tags.copy()
    
    # Remove the sha1 from tags for hash calculation to avoid circular dependency
    tags.pop("sha1", None)
    
    tags_json = json.dumps(tags, sort_keys=True, separators=(",", ":"))
    sha1 = hashlib.sha1(content + tags_json.encode('utf-8')).hexdigest()

    return sha1


# Pydantic models for API
TreeItem_Pydantic = pydantic_model_creator(TreeItem, name="TreeItem")
TreeItemIn_Pydantic = pydantic_model_creator(TreeItem, name="TreeItemIn", exclude_readonly=True)

# Backward compatibility aliases
File = TreeItem
Collection = TreeItem
File_Pydantic = TreeItem_Pydantic
FileIn_Pydantic = TreeItemIn_Pydantic
Collection_Pydantic = TreeItem_Pydantic
CollectionIn_Pydantic = TreeItemIn_Pydantic

# Legacy function alias
calculate_file_obj_hash = calculate_tree_item_hash
