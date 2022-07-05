import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from idp_schedule_provider.forecaster.controller import insert_rows
from idp_schedule_provider.forecaster.database import get_db_session
from idp_schedule_provider.forecaster.models import Scenarios
from idp_schedule_provider.main import app


@pytest.fixture(scope="module")
def test_client():
    yield TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    with mock.patch.dict(os.environ, {"SQLALCHEMY_DATABASE_URL": ":memory:"}):
        yield from get_db_session()


@pytest.fixture()
def database_client(db_session: Session):
    db_session.info["test_session"] = True

    def get_test_session():
        yield db_session

    # use the test session
    app.dependency_overrides[get_db_session] = get_test_session
    with db_session.begin() as xact:
        yield db_session
        xact.rollback()
    app.dependency_overrides = {}


@pytest.fixture()
def scenario_seed(database_client: Session):
    insert_rows(
        database_client,
        [
            Scenarios(id="sce1", name="Scenario 1", description="Test Scenario 1"),
        ],
    )
