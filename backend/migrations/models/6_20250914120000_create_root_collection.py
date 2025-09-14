from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Create the root collection as a real TreeItem with a fixed UUID
        -- Using a well-known UUID for the root collection: 00000000-0000-0000-0000-000000000000
        
        -- First create a Collection entry
        INSERT INTO "collections" (
            "id", 
            "created_at", 
            "updated_at"
        ) VALUES (
            '00000000-0000-0000-0000-000000000000',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        ) ON CONFLICT (id) DO NOTHING;
        
        -- Then create the TreeItem entry for the root collection
        INSERT INTO "tree_items" (
            "id",
            "name", 
            "object_type",
            "object_id",
            "tags",
            "path",
            "permissions",
            "created_at",
            "updated_at"
        ) VALUES (
            '00000000-0000-0000-0000-000000000000',
            'Root',
            'collection',
            '00000000-0000-0000-0000-000000000000',
            '{"description": "Root collection of the file system"}',
            'root',
            420,  -- 0o644 in decimal (rw-r--r--)
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        ) ON CONFLICT (id) DO NOTHING;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Remove the root collection TreeItem and Collection entries
        DELETE FROM "tree_items" WHERE "id" = '00000000-0000-0000-0000-000000000000';
        DELETE FROM "collections" WHERE "id" = '00000000-0000-0000-0000-000000000000';
    """
