import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from idp_schedule_provider.forecaster.database import get_db_session
from idp_schedule_provider.main import app


@pytest.fixture(scope="module")
def test_client():
    yield TestClient(app)


@pytest.fixture(scope="module")
def database_client():
    with mock.patch.dict(os.environ, {"SQLALCHEMY_DATABASE_URL": ":memory:"}):
        yield from get_db_session()
