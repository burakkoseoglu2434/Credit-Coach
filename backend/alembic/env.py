import os

from alembic import context
from sqlalchemy import create_engine

url = (
    context.config.get_main_option("sqlalchemy.url")
    or os.environ.get("CREDIT_COACH_OWNER_DB_URL")
    or os.environ["CREDIT_COACH_TEST_DB_URL"]
)
with create_engine(url).begin() as connection:
    context.configure(connection=connection, target_metadata=None)
    with context.begin_transaction():
        context.run_migrations()
