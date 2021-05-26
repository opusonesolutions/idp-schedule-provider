import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient

# tests for compliance of the authorization token API and authorization system.


@pytest.fixture(autouse=True, scope="module")
def enable_auth():
    with mock.patch.dict(os.environ, {"AUTH": "TRUE"}):
        yield


@pytest.fixture(scope="module")
def auth_token(test_client: TestClient):
    response = test_client.post(
        "/token",
        {
            "grant_type": "client_credentials",
            "client_id": "gridos",
            "client_secret": "gridos_pw",
        },
    )
    yield response.json()["access_token"]


def test_scenario_requires_auth(test_client: TestClient):
    response = test_client.get("/scenario")
    assert response.status_code == 401


def test_scenario_with_token(test_client: TestClient, auth_token: str):
    response = test_client.get("/scenario", headers={"authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200


def test_schedule_requires_auth(test_client: TestClient):
    response = test_client.get("/not_a_scenario/asset_schedules")
    assert response.status_code == 401


def test_schedule_with_token(test_client: TestClient, auth_token: str):
    response = test_client.get(
        "/not_a_scenario/asset_schedules",
        headers={"authorization": f"Bearer {auth_token}"},
        params={
            "start_datetime": "2000-01-01T00:00:00Z",
            "end_datetime": "2000-01-01T23:59:59.999999Z",
            "time_interval": "1 hour",
            "interpolation_method": "linear",
            "sampling_mode": "weighted_average",
            "feeders": ["fd1"],
        },
    )
    assert response.status_code == 404


def test_timespan_requires_auth(test_client: TestClient):
    response = test_client.get("/not_a_scenario/asset_schedules/timespan")
    assert response.status_code == 401


def test_timespan_with_token(test_client: TestClient, auth_token: str):
    response = test_client.get(
        "/not_a_scenario/asset_schedules/timespan",
        headers={"authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 404
