from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio
import os
import sys

# Add the parent directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.base import Base

# Import all models to ensure they're registered
from app.db.models import *  # This will import everything from __init__.py


def include_object(obj, name, type_, reflected, compare_to):
    """
    Safeguard: Prevent Alembic from proposing DROP TABLE for tables that exist in DB
    but are not currently tracked in the models layer.
    """
    if type_ == "table" and reflected and compare_to is None:
        # Table exists in DB (reflected=True) but has no matching model (compare_to=None)
        # We return False to tell Alembic to ignore this 'orphaned' table instead of dropping it.
        return False
    return True


config = context.config

# Override sqlalchemy.url with actual DATABASE_URL
# First try to get from settings, then from environment variable directly
database_url = settings.DATABASE_URL
if not database_url or database_url == "":
    database_url = os.getenv("DATABASE_URL", "")

if not database_url:
    raise ValueError(
        "DATABASE_URL is not set. Please set it in .env file or as environment variable."
    )

from sqlalchemy.engine.url import make_url

print(f"DEBUG: Alembic using database_url: {database_url}")

# Parse and clean URL to remove conflicting query parameters
try:
    url_obj = make_url(database_url)
    if url_obj.query:
        print(f"DEBUG: Stripping query params from URL: {url_obj.query}")
        database_url = url_obj._replace(query={}).render_as_string(hide_password=False)
except Exception as e:
    print(f"WARNING: Failed to parse/clean URL: {e}")

config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Force disable prepared statements for Supabase/PgBouncer
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": lambda: "",
    }

    print(f"DEBUG: Alembic database_url={database_url}")
    print(f"DEBUG: Alembic connect_args={connect_args}")

    if "supabase.com" in database_url:
        connect_args["ssl"] = "require"

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
        url=database_url, # Use the clean URL
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
