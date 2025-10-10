from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE EXTENSION IF NOT EXISTS ltree;
    
        CREATE TABLE IF NOT EXISTS "collections" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL DEFAULT 'New Collection',
    "tags" JSONB NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "path" LTREE NOT NULL DEFAULT 'root'
);
CREATE TABLE IF NOT EXISTS "files" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "original_name" VARCHAR(255) NOT NULL,
    "file_path" VARCHAR(500) NOT NULL,
    "file_size" BIGINT NOT NULL,
    "mime_type" VARCHAR(100) NOT NULL,
    "base_file_type" VARCHAR(20) NOT NULL DEFAULT 'raw',
    "tags" JSONB NOT NULL,
    "sha1" VARCHAR(40) UNIQUE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "path" LTREE NOT NULL DEFAULT 'root'
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


MODELS_STATE = (
    "eJztWW1P2zAQ/iuRPzGJoTZtKUMTUoEyOkGZoGwTCEVu7KYWqR0SZ8BQ//tsN+8hbRcaPp"
    "R+aZu7y93leS627/oCJgxh29s5ITYG+9oLgI4jvgMx2NYAhRMcS2aGQszhUN0BRkKgDAlF"
    "+En83Ndu78TlBFJoYSQuqW/bQgCHHnehyYVkBG0PC5Fzb4wItpGKHAYiSHrzKXnw5TV3fW"
    "mK8Aj6trwZfB351OSEUc33CdqRH82DOAMU3yQjB3mGIdHQMJntT2gcCjFTZEaoFedqYYpd"
    "yJWv8E6VqcGfHZXl9XXv+ETlLlQmo/LZCOXy8V+mKl/PdIkj04zdOs98zGjkQ6UvHYFZYn"
    "EE5QZIm6PTzuVWY/eTNHGYxy1XKVV8MJ2+nv4owDUmQ59kJExnGQmCHCZEMSHqO0lJhGXE"
    "SRA3JiA0WcRA6LsUB0dj6BZxIOrvybAxtfhYXOqt1rKkCCdz6PjZuVSMCIeKEiYqevYe9A"
    "OVPtNJamIImUssQqFtVIllLsiagypXHsOBIpeKAE0FqBjMVq22WjCFw0Iwle4VMD3yt7Lq"
    "TAUoBeYhsXqUF8JpSaPPX3S90WjrtcbuXqvZbrf2anvCVqWVV7WXhVwEmQP5Ye9brz9Igy"
    "0FaYQnZIJnDitCOBWg4nKtr7pc63PKtZ4v1yH0sKFKaglEgQsfQSlI82GqXlNXDKtejKqe"
    "A5VDy1sEZXz4GvrE5oR6O4iY/KAcvmHEUqh+v7rov/UIdk2F9lY+wbZmE4/fzcFUxpPqie"
    "c92Ekst847v7MwH51dHGbPbNLBYQZzbwzr88+7ufUgf7gN70lCGzquuGCbKy7YZnHBNnMF"
    "a7pYPoYBedk1FfqcGZQ9/kfNpoOWgvdYaLlYrQshFiHQBbWfA26XhRgFfnfCHyDxiAZEKF"
    "Urr9Ew6J13rwad8x+pQj/uDLpSoyvpc0a6tZuhLHKi/eoNTjV5qd1c9LvZ9yGyG9xkiPUd"
    "tDpil2wG0zE3vFbB6xKndeAyxsvtJm86qp8NXFxI3GrWuLPBZbcrELkr8jaDxeDMwnyMXR"
    "B05kNo3j9CFxm5vj7SZNp5mW8wsOlgl5hjsMxsJzDdTkx3YCR6r/HOEttd+VlO4CvN/OKm"
    "Qq832829xm4z6iUiyYpaiLBdqH6a8we7nsyz5Lq6iIaE+zUfP8i3qSIQA9dr3sOJ5DimpX"
    "f4hee02P3Hai/edXs5YraNzSDO4i0mYZ7cZsxIvPkr4YP/lQD6+FFLl8nmb4WCLWgzsHn/"
    "gc1m5rCmvelm5rCevG5mDu80c5j+Az7a9Jc="
)
