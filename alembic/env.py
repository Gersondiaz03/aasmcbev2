import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.core.config import settings  # Asegúrate de tener esto bien
from app.models import Base  # Y que todos los modelos estén importados en __init__.py

config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

# Sobrescribe la URL con la de settings (que viene de .env)
config.set_main_option("sqlalchemy.url", str(settings.database_url))

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    url = config.get_main_option("sqlalchemy.url")
    if url is None:
        raise ValueError("No sqlalchemy.url found in Alembic config.")
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
