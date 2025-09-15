# migrations/env.py  (version synchrone)
from __future__ import annotations
import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine, pool

# Optionnel : charger .env si présent
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv()
except Exception:
    pass

# Alembic Config
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Si tu as un Base SQLAlchemy, importe-le et mets target_metadata = Base.metadata
# from src.core.db import Base
target_metadata = None  # ou Base.metadata

def _resolve_db_url() -> str:
    """
    Priorité :
      1) alembic -x db_url=...
      2) variable d'env DB_URL
      3) alembic.ini -> sqlalchemy.url
    """
    xargs = context.get_x_argument(as_dictionary=True)
    if "db_url" in xargs and xargs["db_url"]:
        return xargs["db_url"]

    env_url = os.getenv("DB_URL")
    if env_url:
        return env_url

    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url and ini_url.strip() and ini_url.strip().lower() != "none":
        return ini_url

    raise RuntimeError(
        "Database URL introuvable. Fournis-la via:\n"
        "  - `alembic -x db_url=... upgrade head`\n"
        "  - ou variable d'environnement DB_URL\n"
        "  - ou `alembic.ini -> sqlalchemy.url`"
    )

def run_migrations_offline() -> None:
    url = _resolve_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    url = _resolve_db_url()
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
