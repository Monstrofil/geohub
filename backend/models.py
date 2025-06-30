from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.contrib.postgres.fields import ArrayField

import hashlib
from pathlib import Path

from typing import Dict, Any
import json


class File(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    original_name = fields.CharField(max_length=255)
    file_path = fields.CharField(max_length=500)
    file_size = fields.BigIntField()
    mime_type = fields.CharField(max_length=100)
    base_file_type = fields.CharField(max_length=20, default="raw")  # raster, vector, raw
    tags = fields.JSONField(default=dict)
    sha1 = fields.CharField(max_length=40, unique=True, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "files"

    def __str__(self):
        return f"File(id={self.id}, name='{self.name}', type='{self.base_file_type}')"
    

def calculate_file_obj_hash(file_obj: File):
    content = Path(file_obj.file_path).read_bytes()
    tags = file_obj.tags

    tags_json = json.dumps(tags, sort_keys=True, separators=(",", ":"))
    sha1 = hashlib.sha1(content + tags_json.encode('utf-8')).hexdigest()

    return sha1


# Pydantic models for API
File_Pydantic = pydantic_model_creator(File, name="File")
FileIn_Pydantic = pydantic_model_creator(File, name="FileIn", exclude_readonly=True)


class Tree(models.Model):
    id = fields.CharField(pk=True, max_length=40)  # hash of entries
    entries = ArrayField(element_type="varchar(40)")


class TreeEntry(models.Model):
    id = fields.IntField(pk=True)
    sha1 = fields.CharField(max_length=40)
    object_type = fields.CharField(max_length=10)
    object_id = fields.IntField()


class Commit(models.Model):
    id = fields.CharField(pk=True, max_length=40)  # hash of commit
    tree = fields.ForeignKeyField('models.Tree', related_name='commits')
    parent = fields.ForeignKeyField('models.Commit', related_name='children', null=True)
    message = fields.CharField(max_length=255)
    timestamp = fields.DatetimeField(auto_now_add=True)


class Ref(models.Model):
    name = fields.CharField(pk=True, max_length=100)
    commit = fields.ForeignKeyField('models.Commit', related_name='refs')

    class Meta:
        table = "refs"
