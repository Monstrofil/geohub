from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Add is_georeferenced column to geo_raster_files table
        ALTER TABLE "geo_raster_files" ADD COLUMN "is_georeferenced" BOOLEAN DEFAULT FALSE;
        
        -- Update existing records to set is_georeferenced based on whether they have a map_config_path
        UPDATE "geo_raster_files" SET "is_georeferenced" = TRUE WHERE "map_config_path" IS NOT NULL;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Remove is_georeferenced column from geo_raster_files table
        ALTER TABLE "geo_raster_files" DROP COLUMN "is_georeferenced";
    """
