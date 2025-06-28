from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
from typing import Dict, Any
import json


class File(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    original_name = fields.CharField(max_length=255)
    file_path = fields.CharField(max_length=500)
    file_size = fields.BigIntField()
    mime_type = fields.CharField(max_length=100)
    tags = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "files"

    def __str__(self):
        return f"File(id={self.id}, name='{self.name}')"


class Tag(models.Model):
    id = fields.IntField(pk=True)
    file = fields.ForeignKeyField('models.File', related_name='tag_entries')
    key = fields.CharField(max_length=100)
    value = fields.CharField(max_length=500)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "tags"
        unique_together = (("file", "key"),)

    def __str__(self):
        return f"Tag(id={self.id}, file_id={self.file_id}, {self.key}={self.value})"


# Pydantic models for API
File_Pydantic = pydantic_model_creator(File, name="File")
FileIn_Pydantic = pydantic_model_creator(File, name="FileIn", exclude_readonly=True)
Tag_Pydantic = pydantic_model_creator(Tag, name="Tag")
TagIn_Pydantic = pydantic_model_creator(Tag, name="TagIn", exclude_readonly=True) 