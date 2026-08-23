import re
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Make app importable from alembic/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from app.database import Base

# Import all models so Base.metadata knows every table
import app.models.staff          # noqa: F401
import app.models.transaction    # noqa: F401
import app.models.follow_up_task # noqa: F401
import app.models.evidence_log   # noqa: F401


def _redacted(url: str) -> str:
    """Mask credentials so a target-DB confirmation prompt is safe to print."""
    return re.sub(r"://[^:]+:[^@]+@", "://***:***@", url)


if settings.ENV == "production" and os.getenv("ALEMBIC_CONFIRM_PRODUCTION") != "1":
    sys.exit(
        "Refusing to run migrations: ENV=production "
        f"(target: {_redacted(settings.DATABASE_URL)}).\n"
        "This is a real safety check, not a bug — migrating production is "
        "sometimes intentional (see docs/render-env-setup.md), so it's not "
        "blocked outright. Set ALEMBIC_CONFIRM_PRODUCTION=1 to confirm you "
        "mean to run this against production."
    )

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point autogenerate at our ORM metadata
target_metadata = Base.metadata

# Override the sqlalchemy.url from alembic.ini with our app's DATABASE_URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
