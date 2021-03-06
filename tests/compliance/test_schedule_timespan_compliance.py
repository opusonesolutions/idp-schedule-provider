# tests for compliance of the schedule timespan API
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from idp_schedule_provider.forecaster.controller import insert_rows
from idp_schedule_provider.forecaster.models import ScheduleData


@pytest.fixture()
def data_seed(database_client: Session, scenario_seed):
    forecast_rows = []
    # add a switch with only a single timepoint
    forecast_rows.append(
        ScheduleData(
            scenario_id="sce1",
            asset_name="Switch 1",
            feeder="20KV",
            data={},
            timestamp=datetime(2000, 1, 1, tzinfo=timezone.utc),
        )
    )
    # add a feeder with two timepoints
    forecast_rows.extend(
        [
            ScheduleData(
                scenario_id="sce1",
                asset_name="11KV",
                feeder="11KV",
                data={},
                timestamp=datetime(2000, 1, 1, tzinfo=timezone.utc),
            ),
            ScheduleData(
                scenario_id="sce1",
                asset_name="11KV",
                feeder="11KV",
                data={},
                timestamp=datetime(2009, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc),
            ),
        ]
    )
    # add a load with two timepoints
    forecast_rows.extend(
        [
            ScheduleData(
                scenario_id="sce1",
                asset_name="Load 1",
                feeder="11KV",
                data={},
                timestamp=datetime(2000, 1, 1, tzinfo=timezone.utc),
            ),
            ScheduleData(
                scenario_id="sce1",
                asset_name="Load 1",
                feeder="11KV",
                data={},
                timestamp=datetime(2000, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc),
            ),
        ]
    )

    insert_rows(database_client, forecast_rows)


def test_get_schedule_timespan_missing_scenario(test_client: TestClient):
    response = test_client.get("/missing_scenario/asset_schedules/timespan")
    assert response.status_code == 404


def test_get_schedule_timespan_none(test_client: TestClient, scenario_seed):
    response = test_client.get("/sce1/asset_schedules/timespan")
    assert response.status_code == 200
    assert response.json() == {"assets": {}}


def test_get_schedule_timespans(test_client: TestClient, data_seed):
    response = test_client.get("/sce1/asset_schedules/timespan")
    assert response.status_code == 200
    assert response.json() == {
        "assets": {
            "11KV": {
                "start_datetime": "2000-01-01T00:00:00+00:00",
                "end_datetime": "2009-12-31T23:59:59.999999+00:00",
            },
            "Load 1": {
                "start_datetime": "2000-01-01T00:00:00+00:00",
                "end_datetime": "2000-12-31T23:59:59.999999+00:00",
            },
            "Switch 1": {
                "start_datetime": "2000-01-01T00:00:00+00:00",
                "end_datetime": "2000-01-01T00:00:00+00:00",
            },
        }
    }


def test_get_schedule_timespans_by_feeder(test_client: TestClient, data_seed):
    response = test_client.get("/sce1/asset_schedules/timespan", params={"feeders": ["11KV"]})
    assert response.status_code == 200
    assert response.json() == {
        "assets": {
            "11KV": {
                "start_datetime": "2000-01-01T00:00:00+00:00",
                "end_datetime": "2009-12-31T23:59:59.999999+00:00",
            },
            "Load 1": {
                "start_datetime": "2000-01-01T00:00:00+00:00",
                "end_datetime": "2000-12-31T23:59:59.999999+00:00",
            },
        }
    }


def test_get_schedule_timespan_by_asset_name(test_client: TestClient, data_seed):
    response = test_client.get("/sce1/asset_schedules/timespan", params={"asset_name": "Load 1"})
    assert response.status_code == 200
    assert response.json() == {
        "assets": {
            "Load 1": {
                "start_datetime": "2000-01-01T00:00:00+00:00",
                "end_datetime": "2000-12-31T23:59:59.999999+00:00",
            },
        }
    }


def test_get_schedule_timespans_by_asset_name_and_feeder(test_client: TestClient, data_seed):
    response = test_client.get(
        "/sce1/asset_schedules/timespan", params={"asset_name": "Load 1", "feeders": ["11KV"]}
    )
    assert response.status_code == 200
    assert response.json() == {
        "assets": {
            "Load 1": {
                "start_datetime": "2000-01-01T00:00:00+00:00",
                "end_datetime": "2000-12-31T23:59:59.999999+00:00",
            },
        }
    }
