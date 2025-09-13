from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "geo_raster_files" DROP COLUMN "image_width";
        ALTER TABLE "geo_raster_files" DROP COLUMN "image_height";
        ALTER TABLE "geo_raster_files" DROP COLUMN "image_bands";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "geo_raster_files" ADD "image_width" INT;
        ALTER TABLE "geo_raster_files" ADD "image_height" INT;
        ALTER TABLE "geo_raster_files" ADD "image_bands" INT;"""
