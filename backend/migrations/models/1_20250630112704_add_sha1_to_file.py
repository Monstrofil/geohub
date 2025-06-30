from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "files" ADD "sha1" VARCHAR(40)  UNIQUE;
        CREATE UNIQUE INDEX "uid_files_sha1_a0e942" ON "files" ("sha1");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "idx_files_sha1_a0e942";
        ALTER TABLE "files" DROP COLUMN "sha1";"""
