import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Debug: Output database URL for troubleshooting
print(f"Database URL type: {type(settings.database_url)}")
print(f"Database URL: {settings.database_url}")

# Make sure we have a valid database URL
db_url = str(settings.database_url)
if db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
    # Convert postgresql:// to postgresql+asyncpg:// if not already set
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    print(f"Converted URL: {db_url}")

try:
    engine = create_async_engine(
        db_url,
        echo=True,
        future=True,
        # Added parameters for better connection management
        pool_pre_ping=True,
        pool_recycle=300,
    )
    print("Engine created successfully")
except Exception as e:
    print(f"Database connection error: {e}")
    raise

# Use async_sessionmaker for async engine
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
