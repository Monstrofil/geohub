from tortoise import Tortoise
import os


TORTOISE_ORM = {
    "connections": {
        "default": f"postgres://{os.getenv('DB_USER', 'tagger_user')}:"
                   f"{os.getenv('DB_PASSWORD', 'tagger_password')}@"
                   f"{os.getenv('DB_HOST', 'postgres')}:{os.getenv('DB_PORT', '5432')}/"
                   f"{os.getenv('DB_NAME', 'tagger_db')}"
    },
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


async def init_db():
    await Tortoise.init(
        db_url=TORTOISE_ORM["connections"]["default"],
        modules={"models": TORTOISE_ORM["apps"]["models"]["models"]}
    )


async def close_db():
    """Close database connection"""
    await Tortoise.close_connections() 