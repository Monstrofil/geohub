from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DELETE FROM "tree_items";
        CREATE TABLE IF NOT EXISTS "collections" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "collections" IS 'Model for collections/folders - name and description are stored in TreeItem.tags';
        ALTER TABLE "tree_items" ADD "object_id" UUID NOT NULL;
        ALTER TABLE "tree_items" ADD "object_type" VARCHAR(50) NOT NULL;
        ALTER TABLE "tree_items" DROP COLUMN "type";
        CREATE TABLE IF NOT EXISTS "geo_raster_files" (
    "id" UUID NOT NULL PRIMARY KEY,
    "original_name" VARCHAR(500) NOT NULL,
    "file_path" VARCHAR(1000) NOT NULL,
    "original_file_path" VARCHAR(1000),
    "file_size" BIGINT NOT NULL,
    "mime_type" VARCHAR(200) NOT NULL,
    "image_width" INT,
    "image_height" INT,
    "image_bands" INT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "geo_raster_files" IS 'Model for georeferenced raster files - metadata stored in TreeItem.tags';
        CREATE TABLE IF NOT EXISTS "raw_files" (
    "id" UUID NOT NULL PRIMARY KEY,
    "original_name" VARCHAR(500) NOT NULL,
    "file_path" VARCHAR(1000) NOT NULL,
    "file_size" BIGINT NOT NULL,
    "mime_type" VARCHAR(200) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "raw_files" IS 'Model for raw files - metadata stored in TreeItem.tags';
        CREATE INDEX IF NOT EXISTS "idx_tree_items_object__36e02d" ON "tree_items" ("object_type", "object_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_tree_items_object__36e02d";
        ALTER TABLE "tree_items" ADD "type" VARCHAR(20) NOT NULL;
        ALTER TABLE "tree_items" DROP COLUMN "object_id";
        ALTER TABLE "tree_items" DROP COLUMN "object_type";
        DROP TABLE IF EXISTS "geo_raster_files";
        DROP TABLE IF EXISTS "collections";
        DROP TABLE IF EXISTS "raw_files";"""
