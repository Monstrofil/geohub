from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "task_records" (
    "task_id" VARCHAR(255) NOT NULL PRIMARY KEY,
    "item_type" VARCHAR(255) NOT NULL,
    "item_id" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
        CREATE INDEX IF NOT EXISTS "idx_task_records_item_type" ON "task_records" ("item_type");
        CREATE INDEX IF NOT EXISTS "idx_task_records_item_id" ON "task_records" ("item_id");
        CREATE INDEX IF NOT EXISTS "idx_task_records_item_type_item_id" ON "task_records" ("item_type", "item_id");
        CREATE INDEX IF NOT EXISTS "idx_task_records_created_at" ON "task_records" ("created_at");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "task_records";
    """
