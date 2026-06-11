"""Database initialization and management for Tortoise ORM"""

from tortoise import Tortoise
from typing import Optional

DB_URL = "sqlite://:memory:"  # Use in-memory for development, change to file-based for production


async def init_db():
    """Initialize Tortoise ORM database"""
    await Tortoise.init(
        db_url=DB_URL,
        modules={"models": ["models"]},
    )
    await Tortoise.generate_schemas()


async def close_db():
    """Close database connection"""
    await Tortoise.close_connections()


def get_db():
    """Dependency for getting database connection"""
    return Tortoise
