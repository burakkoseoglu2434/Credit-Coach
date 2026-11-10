import os

import pytest
from sqlalchemy import create_engine, text

URL = os.environ.get("CREDIT_COACH_TEST_DB_URL")
pytestmark = pytest.mark.skipif(
    URL is None and not os.environ.get("CI"), reason="CREDIT_COACH_TEST_DB_URL not set"
)


def test_postgres_reachable():
    # In CI the URL is mandatory: a missing URL fails instead of skipping.
    assert URL, "CREDIT_COACH_TEST_DB_URL must be set in CI"
    with create_engine(URL).connect() as c:
        assert c.execute(text("select 1")).scalar() == 1
