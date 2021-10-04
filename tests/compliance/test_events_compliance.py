# tests for compliance of the asset events API
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
            feeder="global_ev",
            data={"pf": 0.9, "p_max": 2400, "start_soc": 75, "total_battery_capacity": 10000},
            start_timestamp=datetime(2000, 1, 1, 14, 0, 0, 0, timezone.utc),
            end_timestamp=datetime(2000, 1, 1, 17, 59, 59, 59, timezone.utc),
        ),
        EventData(
            scenario_id="sce1",
            asset_name="EV",
            feeder="global_ev",
            data={"pf": 0.9, "p_max": 2400, "start_soc": 75, "total_battery_capacity": 10000},
            start_timestamp=datetime(2000, 1, 1, 23, 0, 0, 0, timezone.utc),
            end_timestamp=datetime(2000, 1, 1, 23, 59, 59, 59, timezone.utc),
        ),
    ]

    insert_schedules(database_client, forecast_rows)


def test_get_timespan_missing_scenario(test_client: TestClient):
    response = test_client.get(
        "/missing_scenario/asset_events",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "feeders": ["global_ev"],
        },
    )
    assert response.status_code == 404


def test_get_timespan_none(test_client: TestClient, scenario_seed):
    response = test_client.get(
        "/sce1/asset_events",
        params={
            "start_datetime": datetime(2000, 1, 2, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 2, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "feeders": ["global_ev"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {"assets": {}}


def test_get_event_data_by_feeder(test_client: TestClient, data_seed):
    # as we are storing our data hourly, there is no interpolation/sampling applied
    response = test_client.get(
        "/sce1/asset_events",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "feeders": ["global_ev"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "assets": {
            "EV": [
                {
                    "start_datetime": "2000-01-01T14:00:00+00:00",
                    "end_datetime": "2000-01-01T17:59:59.000059+00:00",
                    "pf": 0.9,
                    "p_max": 2400.0,
                    "start_soc": 75.0,
                    "total_battery_capacity": 10000.0,
                },
                {
                    "start_datetime": "2000-01-01T23:00:00+00:00",
                    "end_datetime": "2000-01-01T23:59:59.000059+00:00",
                    "pf": 0.9,
                    "p_max": 2400.0,
                    "start_soc": 75.0,
                    "total_battery_capacity": 10000.0,
                },
            ],
        },
    }


def test_get_event_data_by_asset(test_client: TestClient, data_seed):
    # as we are storing our data hourly, there is no interpolation/sampling applied
    response = test_client.get(
        "/sce1/asset_events",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "asset_name": "EV",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "assets": {
            "EV": [
                {
                    "start_datetime": "2000-01-01T14:00:00+00:00",
                    "end_datetime": "2000-01-01T17:59:59.000059+00:00",
                    "pf": 0.9,
                    "p_max": 2400.0,
                    "start_soc": 75.0,
                    "total_battery_capacity": 10000.0,
                },
                {
                    "start_datetime": "2000-01-01T23:00:00+00:00",
                    "end_datetime": "2000-01-01T23:59:59.000059+00:00",
                    "pf": 0.9,
                    "p_max": 2400.0,
                    "start_soc": 75.0,
                    "total_battery_capacity": 10000.0,
                },
            ],
        },
    }


@pytest.mark.parametrize(
    "query_start, query_end",
    [
        (
            datetime(2000, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            datetime(2000, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
        ),
        (
            datetime(2000, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            datetime(2000, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
        ),
        (
            datetime(2000, 1, 1, 16, 0, 0, tzinfo=timezone.utc),
            datetime(2000, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
        ),
    ],
)
def test_get_event_data_datetime_filter(
    test_client: TestClient, data_seed, query_start: datetime, query_end: datetime
):
    # only get data within the specified timerange
    response = test_client.get(
        "/sce1/asset_events",
        params={
            "start_datetime": query_start,
            "end_datetime": query_end,
            "feeders": ["global_ev"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "assets": {
            "EV": [
                {
                    "start_datetime": "2000-01-01T14:00:00+00:00",
                    "end_datetime": "2000-01-01T17:59:59.000059+00:00",
                    "pf": 0.9,
                    "p_max": 2400.0,
                    "start_soc": 75.0,
                    "total_battery_capacity": 10000.0,
                },
            ],
        },
    }


@pytest.mark.parametrize(
    "query_start, query_end",
    [
        (
            datetime(2000, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            datetime(2000, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
        ),
        (
            datetime(2000, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            datetime(2000, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
        ),
        (
            datetime(2000, 1, 1, 16, 0, 0, tzinfo=timezone.utc),
            datetime(2000, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
        ),
    ],
)
def test_get_event_data_overlapping_datetime_filter(
    test_client: TestClient, data_seed, query_start: datetime, query_end: datetime
):
    # only get data within the specified timerange
    response = test_client.get(
        "/sce1/asset_events",
        params={
            "start_datetime": query_start,
            "end_datetime": query_end,
            "feeders": ["global_ev"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "assets": {
            "EV": [
                {
                    "start_datetime": "2000-01-01T14:00:00+00:00",
                    "end_datetime": "2000-01-01T17:59:59.000059+00:00",
                    "pf": 0.9,
                    "p_max": 2400.0,
                    "start_soc": 75.0,
                    "total_battery_capacity": 10000.0,
                },
            ],
        },
    }


@pytest.mark.parametrize(
    "query_start, query_end",
    [
        (
            datetime(2000, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            datetime(2000, 1, 1, 13, 59, 59, tzinfo=timezone.utc),
        ),
        (
            datetime(2000, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
            datetime(2000, 1, 1, 19, 0, 0, tzinfo=timezone.utc),
        ),
    ],
)
def test_get_event_data_no_overlap(
    test_client: TestClient, data_seed, query_start: datetime, query_end: datetime
):
    # only get data within the specified timerange
    response = test_client.get(
        "/sce1/asset_events",
        params={
            "start_datetime": query_start,
            "end_datetime": query_end,
            "feeders": ["global_ev"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {"assets": {}}
