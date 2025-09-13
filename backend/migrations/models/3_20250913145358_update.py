from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_raw_files_sha1_29ca0b";
        DROP INDEX IF EXISTS "idx_geo_raster__sha1_d02950";
        ALTER TABLE "collections" DROP COLUMN "description";
        ALTER TABLE "collections" DROP COLUMN "name";
        ALTER TABLE "geo_raster_files" DROP COLUMN "control_points_count";
        ALTER TABLE "geo_raster_files" DROP COLUMN "is_georeferenced";
        ALTER TABLE "geo_raster_files" DROP COLUMN "georeferencing_accuracy";
        ALTER TABLE "geo_raster_files" DROP COLUMN "target_srs";
        ALTER TABLE "geo_raster_files" DROP COLUMN "sha1";
        ALTER TABLE "geo_raster_files" DROP COLUMN "georeferencing_method";
        ALTER TABLE "raw_files" DROP COLUMN "sha1";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "raw_files" ADD "sha1" VARCHAR(40) NOT NULL;
        ALTER TABLE "collections" ADD "description" TEXT;
        ALTER TABLE "collections" ADD "name" VARCHAR(255) NOT NULL;
        ALTER TABLE "geo_raster_files" ADD "control_points_count" INT;
        ALTER TABLE "geo_raster_files" ADD "is_georeferenced" BOOL NOT NULL DEFAULT False;
        ALTER TABLE "geo_raster_files" ADD "georeferencing_accuracy" JSONB;
        ALTER TABLE "geo_raster_files" ADD "target_srs" VARCHAR(100);
        ALTER TABLE "geo_raster_files" ADD "sha1" VARCHAR(40) NOT NULL;
        ALTER TABLE "geo_raster_files" ADD "georeferencing_method" VARCHAR(100);
        CREATE INDEX IF NOT EXISTS "idx_raw_files_sha1_29ca0b" ON "raw_files" ("sha1");
        CREATE INDEX IF NOT EXISTS "idx_geo_raster__sha1_d02950" ON "geo_raster_files" ("sha1");"""
