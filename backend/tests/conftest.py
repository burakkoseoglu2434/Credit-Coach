import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

OWNER = os.environ.get("CREDIT_COACH_TEST_DB_URL")
APP = os.environ.get("CREDIT_COACH_APP_DB_URL")
BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture
def db():
    """Fresh schema per test. Yields (owner_engine, app_engine); app role has INSERT/SELECT only."""
    if not (OWNER and APP):
        if os.environ.get("CI"):
            pytest.fail("CREDIT_COACH_TEST_DB_URL and CREDIT_COACH_APP_DB_URL are required in CI")
        pytest.skip("database URLs not set")
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    cfg.set_main_option("sqlalchemy.url", OWNER.replace("%", "%%"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    owner, app = create_engine(OWNER), create_engine(APP)
    yield owner, app
    owner.dispose()
    app.dispose()
