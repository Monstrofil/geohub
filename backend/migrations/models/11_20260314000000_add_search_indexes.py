from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE INDEX IF NOT EXISTS "idx_tree_items_tags_gin" ON "tree_items" USING GIN ("tags");
        CREATE INDEX IF NOT EXISTS "idx_tree_items_created_at" ON "tree_items" ("created_at");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_tree_items_tags_gin";
        DROP INDEX IF EXISTS "idx_tree_items_created_at";
    """
