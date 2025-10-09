from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "chunked_upload_sessions" (
    "id" UUID NOT NULL PRIMARY KEY,
    "upload_id" VARCHAR(255) NOT NULL UNIQUE,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "filename" VARCHAR(255) NOT NULL,
    "file_size" BIGINT NOT NULL,
    "mime_type" VARCHAR(100),
    "tags" JSONB NOT NULL DEFAULT '{}',
    "parent_path" VARCHAR(500) NOT NULL DEFAULT 'root',
    "chunk_size" BIGINT NOT NULL,
    "total_chunks" INT NOT NULL,
    "chunks_received" JSONB NOT NULL DEFAULT '[]',
    "temp_dir" VARCHAR(500) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMPTZ NOT NULL
);
        CREATE INDEX IF NOT EXISTS "idx_chunked_upload_sessions_upload_id" ON "chunked_upload_sessions" ("upload_id");
        CREATE INDEX IF NOT EXISTS "idx_chunked_upload_sessions_user_id" ON "chunked_upload_sessions" ("user_id");
        CREATE INDEX IF NOT EXISTS "idx_chunked_upload_sessions_expires_at" ON "chunked_upload_sessions" ("expires_at");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "chunked_upload_sessions";
    """
