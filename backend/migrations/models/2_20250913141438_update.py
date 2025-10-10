from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


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


MODELS_STATE = (
    "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"
    "mJ00"
)
