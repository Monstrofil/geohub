from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "trees" (
    "id" VARCHAR(40) NOT NULL  PRIMARY KEY
);
        CREATE TABLE IF NOT EXISTS "commits" (
    "id" VARCHAR(40) NOT NULL  PRIMARY KEY,
    "message" VARCHAR(255) NOT NULL,
    "timestamp" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "parent_id" VARCHAR(40) REFERENCES "commits" ("id") ON DELETE CASCADE,
    "tree_id" VARCHAR(40) NOT NULL REFERENCES "trees" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "tree_entries" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "sha1" VARCHAR(40) NOT NULL,
    "object_type" VARCHAR(10) NOT NULL,
    "object_id" INT NOT NULL,
    "tree_id" VARCHAR(40) NOT NULL REFERENCES "trees" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "commits";
        DROP TABLE IF EXISTS "trees";
        DROP TABLE IF EXISTS "tree_entries";"""
