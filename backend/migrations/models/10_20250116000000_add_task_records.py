from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "task_records" (
    "task_id" VARCHAR(255) NOT NULL PRIMARY KEY,
    "item_type" VARCHAR(255) NOT NULL,
    "item_id" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_task_record_item_ty_0b65f4" ON "task_records" ("item_type");
CREATE INDEX IF NOT EXISTS "idx_task_record_item_id_71d7e4" ON "task_records" ("item_id");
CREATE INDEX IF NOT EXISTS "idx_task_record_item_ty_f6a96c" ON "task_records" ("item_type", "item_id");
CREATE INDEX IF NOT EXISTS "idx_task_record_created_1bfb50" ON "task_records" ("created_at");
COMMENT ON TABLE "task_records" IS 'Model for tracking background task metadata';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "task_records";"""


MODELS_STATE = (
    "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"
    "to"
)