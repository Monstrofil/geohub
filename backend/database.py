from tortoise import Tortoise
import os


TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": os.getenv("DB_HOST", "postgres"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "user": os.getenv("DB_USER", "tagger_user"),
                "password": os.getenv("DB_PASSWORD", "tagger_password"),
                "database": os.getenv("DB_NAME", "tagger_db"),
            }
        }
    },
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "UTC"
}


async def close_db():
    """Close database connection"""
    await Tortoise.close_connections() 