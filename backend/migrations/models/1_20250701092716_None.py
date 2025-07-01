from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "files" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "original_name" VARCHAR(255) NOT NULL,
    "file_path" VARCHAR(500) NOT NULL,
    "file_size" BIGINT NOT NULL,
    "mime_type" VARCHAR(100) NOT NULL,
    "base_file_type" VARCHAR(20) NOT NULL  DEFAULT 'raw',
    "tags" JSONB NOT NULL,
    "sha1" VARCHAR(40)  UNIQUE,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "tree" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "entries" varchar(40)[] NOT NULL
);
CREATE TABLE IF NOT EXISTS "commit" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "message" VARCHAR(255) NOT NULL,
    "timestamp" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "parent_id" UUID REFERENCES "commit" ("id") ON DELETE CASCADE,
    "tree_id" UUID NOT NULL REFERENCES "tree" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "refs" (
    "name" VARCHAR(100) NOT NULL  PRIMARY KEY,
    "commit_id" UUID NOT NULL REFERENCES "commit" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "treeentry" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "path" VARCHAR(40) NOT NULL,
    "object_type" VARCHAR(10) NOT NULL,
    "object_id" INT NOT NULL
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
