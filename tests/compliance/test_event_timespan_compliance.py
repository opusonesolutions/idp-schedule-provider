# tests for compliance of the events timespan API
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from idp_schedule_provider.forecaster.controller import (
    insert_scenarios,
    insert_schedules,
)
from idp_schedule_provider.forecaster.models import EventData, Scenarios


@pytest.fixture()
def scenario_seed(database_client: Session):
    insert_scenarios(
        database_client,
        [
            Scenarios(id="sce1", name="Scenario 1", description="Test Scenario 1"),
        ],
    )


@pytest.fixture()
def data_seed(database_client: Session, scenario_seed):
    forecast_rows = [
        EventData(
            scenario_id="sce1",
            asset_name="EV",
            feeder="F1",
            data={},
            start_timestamp=datetime(2000, 1, 1, 14, 0, 0, 0, timezone.utc),
            end_timestamp=datetime(2000, 1, 1, 17, 59, 59, 999999, timezone.utc),
        ),
        EventData(
            scenario_id="sce1",
            asset_name="EV",
            feeder="F2",
            data={},
            start_timestamp=datetime(2000, 1, 1, 23, 0, 0, 0, timezone.utc),
            end_timestamp=datetime(2000, 1, 1, 23, 59, 59, 999999, timezone.utc),
        ),
        EventData(
            scenario_id="sce1",
            asset_name="EV",
            feeder="F1",
            data={},
            start_timestamp=datetime(2000, 1, 1, 1, 0, 0, 0, timezone.utc),
            end_timestamp=datetime(2000, 1, 1, 2, 59, 59, 999999, timezone.utc),
        ),
        EventData(
            scenario_id="sce1",
            asset_name="EV2",
            feeder="F1",
            data={},
            start_timestamp=datetime(2000, 1, 1, 1, 0, 0, 0, timezone.utc),
            end_timestamp=datetime(2000, 1, 1, 2, 59, 59, 999999, timezone.utc),
        ),
    ]

    insert_schedules(database_client, forecast_rows)


def test_get_timespan_missing_scenario(test_client: TestClient):
    response = test_client.get("/missing_scenario/asset_events/timespan")
    assert response.status_code == 404


def test_get_timespan_none(test_client: TestClient, scenario_seed):
    response = test_client.get("/sce1/asset_events/timespan")
    assert response.status_code == 200
    assert response.json() == {"assets": {}}


def test_get_event_timespans(test_client: TestClient, data_seed):
    response = test_client.get("/sce1/asset_events/timespan")
    assert response.status_code == 200
    assert response.json() == {
        "assets": {
            "EV": {
                "start_datetime": "2000-01-01T01:00:00+00:00",
                "end_datetime": "2000-01-01T23:59:59.999999+00:00",
            },
            "EV2": {
                "start_datetime": "2000-01-01T01:00:00+00:00",
                "end_datetime": "2000-01-01T02:59:59.999999+00:00",
            },
        }
    }


def test_get_event_timespans_by_feeder(test_client: TestClient, data_seed):
    response = test_client.get("/sce1/asset_events/timespan", params={"feeders": ["F1"]})
    assert response.status_code == 200
    assert response.json() == {
        "assets": {
            "EV": {
                "start_datetime": "2000-01-01T01:00:00+00:00",
                "end_datetime": "2000-01-01T17:59:59.999999+00:00",
            },
            "EV2": {
                "start_datetime": "2000-01-01T01:00:00+00:00",
                "end_datetime": "2000-01-01T02:59:59.999999+00:00",
            },
        }
    }


def test_get_event_timespans_by_asset_name(test_client: TestClient, data_seed):
    response = test_client.get("/sce1/asset_events/timespan", params={"asset_name": "EV"})
    assert response.status_code == 200
    assert response.json() == {
        "assets": {
            "EV": {
                "start_datetime": "2000-01-01T01:00:00+00:00",
                "end_datetime": "2000-01-01T23:59:59.999999+00:00",
            },
        }
    }


def test_get_event_timespans_by_asset_name_and_feeder(test_client: TestClient, data_seed):
    response = test_client.get(
        "/sce1/asset_events/timespan", params={"asset_name": "EV", "feeders": ["F1"]}
    )
    assert response.status_code == 200
    assert response.json() == {
        "assets": {
            "EV": {
                "start_datetime": "2000-01-01T01:00:00+00:00",
                "end_datetime": "2000-01-01T17:59:59.999999+00:00",
            },
        }
    }
