from tortoise import BaseDBAsyncClient


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
