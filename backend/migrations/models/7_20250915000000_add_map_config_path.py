from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Add map_config_path column to geo_raster_files table
        ALTER TABLE "geo_raster_files" ADD COLUMN "map_config_path" VARCHAR(1000);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Remove map_config_path column from geo_raster_files table
        ALTER TABLE "geo_raster_files" DROP COLUMN "map_config_path";"""


MODELS_STATE = (
    "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"
    "fRVrGJ"
)
