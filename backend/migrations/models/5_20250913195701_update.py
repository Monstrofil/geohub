from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "tree_items" ADD "permissions" INT NOT NULL DEFAULT 420;
        ALTER TABLE "tree_items" ADD "owner_group_id" UUID;
        ALTER TABLE "tree_items" ADD "owner_user_id" UUID;
        CREATE TABLE IF NOT EXISTS "groups" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "groups" IS 'Group model for organizing users and permissions';
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "password_hash" VARCHAR(128) NOT NULL,
    "salt" VARCHAR(32) NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "is_admin" BOOL NOT NULL DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "users" IS 'User model for authentication and permissions';
        ALTER TABLE "tree_items" ADD CONSTRAINT "fk_tree_ite_groups_546a3879" FOREIGN KEY ("owner_group_id") REFERENCES "groups" ("id") ON DELETE CASCADE;
        ALTER TABLE "tree_items" ADD CONSTRAINT "fk_tree_ite_users_ed2c5b95" FOREIGN KEY ("owner_user_id") REFERENCES "users" ("id") ON DELETE CASCADE;
CREATE TABLE "user_groups" (
    "groups_id" UUID NOT NULL REFERENCES "groups" ("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "tree_items" DROP CONSTRAINT IF EXISTS "fk_tree_ite_users_ed2c5b95";
        ALTER TABLE "tree_items" DROP CONSTRAINT IF EXISTS "fk_tree_ite_groups_546a3879";
        ALTER TABLE "tree_items" DROP COLUMN "permissions";
        ALTER TABLE "tree_items" DROP COLUMN "owner_group_id";
        ALTER TABLE "tree_items" DROP COLUMN "owner_user_id";
        DROP TABLE IF EXISTS "groups";
        DROP TABLE IF EXISTS "users";"""


MODELS_STATE = (
    "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"
)
