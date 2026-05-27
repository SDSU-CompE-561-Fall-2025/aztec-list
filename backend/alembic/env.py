"""
Alembic environment.

Wires Alembic to the running app:

- Pulls the database URL from ``app.core.settings`` so the same env vars that
  drive the API also drive migrations (no separate sqlalchemy.url to keep in
  sync in alembic.ini).
- Imports ``app.models`` so every ORM table is registered on ``Base.metadata``
  before autogenerate runs (otherwise it would emit no DDL).
"""

import importlib
import sys
from logging.config import fileConfig
from pathlib import Path

# Make backend/src importable so we can pull in the FastAPI app's models + settings.
# Done before any `from app...` import below.
_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from sqlalchemy import engine_from_config, pool  # noqa: E402

from alembic import context  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.core.settings import settings  # noqa: E402

# Side-effect import: registers every model class on ``Base.metadata`` so
# autogenerate can see them. Each domain module pulls in the rest via cross-imports.
importlib.import_module("app.models.user")
importlib.import_module("app.models.profile")
importlib.import_module("app.models.listing")
importlib.import_module("app.models.listing_image")
importlib.import_module("app.models.conversation")
importlib.import_module("app.models.message")
importlib.import_module("app.models.admin")
importlib.import_module("app.models.support_ticket")
importlib.import_module("app.models.ai_conversation")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the URL from settings so .env / env vars are the single source of truth.
config.set_main_option("sqlalchemy.url", settings.db.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit raw SQL for the migration without connecting to a database."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Open a real connection and apply migrations against the live schema."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            # Use a batch for SQLite so ALTERs work even on the dev DB.
            render_as_batch=connection.dialect.name == "sqlite",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
