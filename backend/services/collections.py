from models import TreeItem, Collection
import uuid
import datetime
from typing import List, Optional, Dict, Any, Tuple


# Constants
ROOT_COLLECTION_ID = "00000000-0000-0000-0000-000000000000"


class CollectionsService:
    
    @classmethod
    async def create_collection(cls, name: str, tags: dict, parent_path: str = "root"):
        """Create a new collection"""
        # Create LTREE-compatible ID: use 'c' prefix + first 12 chars of UUID hex (no hyphens)
        collection_uuid = str(uuid.uuid4()).replace('-', '')[:12]
        collection_segment = f"c{collection_uuid}"
        
        # Create the path: parent_path.collection_segment
        collection_path = f"{parent_path}.{collection_segment}"
        
        # Create Collection (minimal model - data stored in TreeItem.tags)
        collection = await Collection.create()
        
        # Prepare tags with name and description
        collection_tags = tags.copy() if tags else {}
        
        # Create TreeItem
        tree_item_obj = await TreeItem.create(
            name=name,
            object_type="collection",
            object_id=collection.id,
            path=collection_path,
            tags=collection_tags
        )
        
        return tree_item_obj
    
    @classmethod
    async def get_collection(cls, collection_id: str):
        """Get collection by ID"""
        return await TreeItem.get_or_none(id=collection_id, object_type="collection")
    
    @classmethod
    async def get_collection_by_path(cls, path: str):
        """Get collection by path"""
        return await TreeItem.get_or_none(path=path, object_type="collection")
    
    @classmethod
    async def _update_descendant_paths(cls, old_path: str, new_path: str):
        """Update paths of all descendants when a collection is moved"""
        # Update all tree items that have paths starting with old_path
        from tortoise import connections
        connection = connections.get("default")
        
        # Update all tree items (both files and collections)
        await connection.execute_query(
            "UPDATE tree_items SET path = $1 || subpath(path, nlevel($2)) WHERE path <@ $2 AND path != $2",
            [new_path, old_path]
        )
    
    @classmethod
    async def delete_collection(cls, collection_id: str, force: bool = False):
        """Delete collection and optionally its contents"""
        # Prevent deletion of root collection
        if collection_id == ROOT_COLLECTION_ID:
            raise ValueError("Cannot delete the root collection")
            
        collection = await TreeItem.get_or_none(id=collection_id, object_type="collection")
        if not collection:
            return False
        
        collection_path = collection.path
        
        # Check if collection has contents using LTREE operators
        if not force:
            from tortoise import connections
            connection = connections.get("default")
            
            # Check for any items in this collection or its descendants
            item_count = await connection.execute_query_dict(
                "SELECT COUNT(*) as count FROM tree_items WHERE path <@ $1 AND path != $1",
                [collection_path]
            )
            
            if item_count[0]['count'] > 0:
                raise ValueError("Collection is not empty. Use force=True to delete anyway.")
        
        # If force=True, delete all contents first
        if force:
            from tortoise import connections
            connection = connections.get("default")
            
            # Delete all items in this collection and its descendants
            await connection.execute_query(
                "DELETE FROM tree_items WHERE path <@ $1 AND path != $1",
                [collection_path]
            )
        
        await collection.delete()
        return True
    
    @classmethod
    async def list_collection_contents(cls, collection_path: str = "root", skip: int = 0, limit: int = 100):
        """List files and subcollections in a collection as one iterable"""
        # Use raw SQL with proper parameterization and manual model instantiation
        from tortoise import connections
        
        connection = connections.get("default")
        
        # Construct regex pattern safely - escape special characters for PostgreSQL regex
        # Pattern matches paths that are direct children of collection_path
        regex_pattern = f"{collection_path}.*{{1}}"
        
        # Use parameterized query to prevent SQL injection
        query = """
            SELECT * FROM tree_items 
            WHERE path ~ $1 
            ORDER BY created_at 
            OFFSET $2 LIMIT $3
        """
        
        # Execute raw query and get results
        results = await connection.execute_query_dict(query, [regex_pattern, skip, limit])
        
        # Manually instantiate TreeItem objects with proper field mapping
        items = []
        for row in results:
            # Create TreeItem instance with all fields
            item = TreeItem(
                id=row['id'],
                name=row['name'],
                object_type=row['object_type'],
                object_id=row['object_id'],
                tags=row['tags'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                path=row['path'],
                permissions=row['permissions'],
            )
            item.owner_user_id = row.get('owner_user_id')
            item.owner_group_id = row.get('owner_group_id')
            # Mark as fetched from DB so it behaves like a proper model instance
            item._saved_in_db = True
            items.append(item)
        
        return items

    @classmethod
    async def search_items(
        cls,
        type: Optional[str] = None,
        object_type: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        collection_path: Optional[str] = None,
        created_after: Optional[datetime.datetime] = None,
        created_before: Optional[datetime.datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[TreeItem], int]:
        """Search tree items with filters. Returns (items, total_count)."""
        from tortoise import connections
        import json

        connection = connections.get("default")

        conditions = []
        params = []
        param_idx = 1

        # Filter by high-level type ("file" or "collection")
        if type == "file":
            conditions.append("object_type IN ('raw_file', 'geo_raster_file')")
        elif type == "collection":
            conditions.append("object_type = 'collection'")

        # Filter by specific object_type
        if object_type:
            conditions.append(f"object_type = ${param_idx}")
            params.append(object_type)
            param_idx += 1

        # Filter by tags: null value = key exists (any value), otherwise exact match
        if tags:
            # Split into key-existence checks (null) and exact-match checks (non-null)
            exact_match = {k: v for k, v in tags.items() if v is not None}
            key_exists = [k for k, v in tags.items() if v is None]

            if exact_match:
                conditions.append(f"tags @> ${param_idx}::jsonb")
                params.append(json.dumps(exact_match))
                param_idx += 1

            for key in key_exists:
                conditions.append(f"tags ? ${param_idx}")
                params.append(key)
                param_idx += 1

        # Filter by name (case-insensitive substring)
        # Escape ILIKE special characters so user input is treated literally
        if name:
            escaped_name = name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            conditions.append(f"name ILIKE ${param_idx}")
            params.append(f"%{escaped_name}%")
            param_idx += 1

        # Scope to collection subtree
        if collection_path:
            conditions.append(f"path <@ ${param_idx}")
            params.append(collection_path)
            param_idx += 1

        # Date range filters
        if created_after:
            conditions.append(f"created_at >= ${param_idx}")
            params.append(created_after)
            param_idx += 1

        if created_before:
            conditions.append(f"created_at <= ${param_idx}")
            params.append(created_before)
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM tree_items WHERE {where_clause}"
        count_result = await connection.execute_query_dict(count_query, list(params))
        total = count_result[0]["count"]

        # Get paginated results (use a copy of params to avoid mutation issues)
        data_params = list(params)
        data_params.extend([skip, limit])
        data_query = f"""
            SELECT * FROM tree_items
            WHERE {where_clause}
            ORDER BY created_at DESC
            OFFSET ${param_idx} LIMIT ${param_idx + 1}
        """

        results = await connection.execute_query_dict(data_query, data_params)

        items = []
        for row in results:
            item = TreeItem(
                id=row["id"],
                name=row["name"],
                object_type=row["object_type"],
                object_id=row["object_id"],
                tags=row["tags"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                path=row["path"],
                permissions=row["permissions"],
            )
            item.owner_user_id = row.get("owner_user_id")
            item.owner_group_id = row.get("owner_group_id")
            item._saved_in_db = True
            items.append(item)

        return items, total
