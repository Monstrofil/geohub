import pytest
import asyncio
import os
import pytest_asyncio
from tortoise import Tortoise
from database import TORTOISE_ORM


def get_database_url():
    """Get database URL from environment variables."""
    # Use DATABASE_URL if available, otherwise fall back to TORTOISE_ORM config
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    # Fall back to TORTOISE_ORM configuration
    return TORTOISE_ORM["connections"]["default"]


@pytest_asyncio.fixture(autouse=True)
async def initialize_tests():
    """Initialize and cleanup database for each test."""
    database_url = get_database_url()
    
    # Initialize Tortoise directly instead of using the test helper
    await Tortoise.init(
        db_url=database_url,
        modules={"models": TORTOISE_ORM["apps"]["models"]["models"]}
    )

    for model, class_ in Tortoise.apps.get('models').items():
        print(model, class_)
        await class_.all().delete()
    # Generate schemas
    
    # await Tortoise.generate_schemas()
    
    yield
    
    await Tortoise.close_connections() 