from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "tree" ADD "entries" varchar(40)[] DEFAULT array[]::varchar(40)[] NOT NULL;
        ALTER TABLE "treeentry" DROP COLUMN "tree_id";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "tree" DROP COLUMN "entries";
        ALTER TABLE "treeentry" ADD "tree_id" VARCHAR(40) NOT NULL;"""
