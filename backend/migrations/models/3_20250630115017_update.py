from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "commits" RENAME TO "commit";
        CREATE TABLE IF NOT EXISTS "refs" (
    "name" VARCHAR(100) NOT NULL  PRIMARY KEY,
    "commit_id" VARCHAR(40) NOT NULL REFERENCES "commit" ("id") ON DELETE CASCADE
);
        ALTER TABLE "trees" RENAME TO "tree";
        ALTER TABLE "tree_entries" RENAME TO "treeentry";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "tree" RENAME TO "trees";
        ALTER TABLE "commit" RENAME TO "commits";
        ALTER TABLE "treeentry" RENAME TO "tree_entries";
        DROP TABLE IF EXISTS "refs";"""
