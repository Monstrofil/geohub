from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Add map_config_path column to geo_raster_files table
        ALTER TABLE "geo_raster_files" ADD COLUMN "map_config_path" VARCHAR(1000);
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Remove map_config_path column from geo_raster_files table
        ALTER TABLE "geo_raster_files" DROP COLUMN "map_config_path";
    """
