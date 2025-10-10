from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Add is_georeferenced column to geo_raster_files table
        ALTER TABLE "geo_raster_files" ADD COLUMN "is_georeferenced" BOOLEAN DEFAULT FALSE;
        
        -- Update existing records to set is_georeferenced based on whether they have a map_config_path
        UPDATE "geo_raster_files" SET "is_georeferenced" = TRUE WHERE "map_config_path" IS NOT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Remove is_georeferenced column from geo_raster_files table
        ALTER TABLE "geo_raster_files" DROP COLUMN "is_georeferenced";"""


MODELS_STATE = (
    "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"
    "5tOIWGU2j8+iycQvkyrloe4el/ttoj4w=="
)
