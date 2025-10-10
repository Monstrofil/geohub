from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


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
        CREATE INDEX IF NOT EXISTS "idx_chunked_upload_sessions_expires_at" ON "chunked_upload_sessions" ("expires_at");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "chunked_upload_sessions";"""


MODELS_STATE = (
    "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"
    "jI3N15+P5q3uiuHpf+kHVqk="
)
