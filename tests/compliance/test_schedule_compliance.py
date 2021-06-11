# tests for compliance of the asset schedules API
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from idp_schedule_provider.forecaster.controller import (
    insert_scenarios,
    insert_schedules,
)
from idp_schedule_provider.forecaster.models import ForecastData, Scenarios
from idp_schedule_provider.forecaster.schemas import (
    InterpolationMethod,
    SamplingMode,
    TimeInterval,
)


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
    forecast_rows = []
    # add a switch with only a single timepoint
    forecast_rows.append(
        ForecastData(
            scenario_id="sce1",
            asset_name="Switch 1",
            feeder="20KV",
            data={
                "status": 1.0,
            },
            timestamp=datetime(2000, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
        )
    )
    # add 2 hr of feeder data
    for i in range(3):
        forecast_rows.append(
            ForecastData(
                scenario_id="sce1",
                asset_name="11KV",
                feeder="11KV",
                data={
                    "load": 1400 + i * 10,
                    "load_pf": 0.9,
                    "generation": 1600 - i * 10,
                    "generation_pf": 0.9,
                },
                timestamp=datetime(2000, 1, 1, i, 0, 0, tzinfo=timezone.utc),
            )
        )

    insert_schedules(database_client, forecast_rows)


def test_get_timespan_missing_scenario(test_client: TestClient):
    response = test_client.get(
        "/missing_scenario/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.HOUR_1.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": ["11KV", "20KV"],
        },
    )
    assert response.status_code == 404


def test_get_timespan_none(test_client: TestClient, scenario_seed):
    response = test_client.get(
        "/sce1/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.HOUR_1.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": ["11KV", "20KV"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "time_interval": TimeInterval.HOUR_1.value,
        "assets": {},
        "time_stamps": [],
    }


def test_get_schedule_data_hourly_by_feeder(test_client: TestClient, data_seed):
    # as we are storing our data hourly, there is no interpolation/sampling applied
    response = test_client.get(
        "/sce1/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.HOUR_1.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": ["11KV", "20KV"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "time_interval": TimeInterval.HOUR_1.value,
        "time_stamps": [
            "2000-01-01T00:00:00+00:00",
            "2000-01-01T01:00:00+00:00",
            "2000-01-01T02:00:00+00:00",
        ],
        "assets": {
            "11KV": [
                {
                    "generation": 1600,
                    "generation_pf": 0.9,
                    "load": 1400,
                    "load_pf": 0.9,
                },
                {
                    "generation": 1600 - 10,
                    "generation_pf": 0.9,
                    "load": 1400 + 10,
                    "load_pf": 0.9,
                },
                {
                    "generation": 1600 - 20,
                    "generation_pf": 0.9,
                    "load": 1400 + 20,
                    "load_pf": 0.9,
                },
            ],
            "Switch 1": [{}, {"status": 1.0}, {}],
        },
    }


def test_get_schedule_data_hourly_by_asset(test_client: TestClient, data_seed):
    # only get data within the specified timerange
    response = test_client.get(
        "/sce1/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.HOUR_1.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "asset_name": ["11KV"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "time_interval": TimeInterval.HOUR_1.value,
        "time_stamps": [
            "2000-01-01T00:00:00+00:00",
            "2000-01-01T01:00:00+00:00",
            "2000-01-01T02:00:00+00:00",
        ],
        "assets": {
            "11KV": [
                {
                    "generation": 1600,
                    "generation_pf": 0.9,
                    "load": 1400,
                    "load_pf": 0.9,
                },
                {
                    "generation": 1600 - 10,
                    "generation_pf": 0.9,
                    "load": 1400 + 10,
                    "load_pf": 0.9,
                },
                {
                    "generation": 1600 - 20,
                    "generation_pf": 0.9,
                    "load": 1400 + 20,
                    "load_pf": 0.9,
                },
            ]
        },
    }


def test_get_schedule_data_datetime_filter(test_client: TestClient, data_seed):
    # only get data within the specified timerange
    response = test_client.get(
        "/sce1/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 1, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.HOUR_1.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": ["11KV"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "time_interval": TimeInterval.HOUR_1.value,
        "time_stamps": ["2000-01-01T01:00:00+00:00"],
        "assets": {
            "11KV": [
                {
                    "generation": 1600 - 10,
                    "generation_pf": 0.9,
                    "load": 1400 + 10,
                    "load_pf": 0.9,
                },
            ]
        },
    }


@pytest.mark.parametrize("interval", [TimeInterval.DAY_1, TimeInterval.MONTH_1])
def test_get_schedule_data_sampled(test_client: TestClient, interval: TimeInterval, data_seed):
    # daily or higher implies sampling due to hourly data stored
    response = test_client.get(
        "/sce1/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": interval.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.WEIGHTED_AVERAGE.value,
            "feeders": ["11KV"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "time_interval": interval.value,
        "time_stamps": ["2000-01-01T00:00:00+00:00"],
        "assets": {
            "11KV": [
                {
                    "generation": 1590,
                    "generation_pf": 0.9,
                    "load": 1410,
                    "load_pf": 0.9,
                }
            ]
        },
    }


def test_get_schedule_data_sampled_unsupported(test_client: TestClient, data_seed):
    # This tests shows the expected behavior when sampling to an unsupported interval
    response = test_client.get(
        "/sce1/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.YEAR_1.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": ["11KV"],
        },
    )
    assert response.status_code == 404


@pytest.mark.parametrize("interval", [TimeInterval.MIN_15])
def test_get_schedule_data_interpolated(test_client: TestClient, interval: TimeInterval, data_seed):
    # daily or higher implies sampling due to hourly data stored
    # 30 min intervel behavior should be the same aside from having half as many new datapoints
    response = test_client.get(
        "/sce1/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 2, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": interval.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": ["11KV"],
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "time_interval": interval.value,
        "time_stamps": [
            "2000-01-01T01:00:00+00:00",
            "2000-01-01T01:15:00+00:00",
            "2000-01-01T01:30:00+00:00",
            "2000-01-01T01:45:00+00:00",
            "2000-01-01T02:00:00+00:00",
            "2000-01-01T02:15:00+00:00",
            "2000-01-01T02:30:00+00:00",
            "2000-01-01T02:45:00+00:00",
        ],
        "assets": {
            "11KV": [
                {"generation": 1590, "generation_pf": 0.9, "load": 1410, "load_pf": 0.9},
                {"generation": 1587.5, "generation_pf": 0.9, "load": 1412.5, "load_pf": 0.9},
                {"generation": 1585, "generation_pf": 0.9, "load": 1415, "load_pf": 0.9},
                {"generation": 1582.5, "generation_pf": 0.9, "load": 1417.5, "load_pf": 0.9},
                {"generation": 1580, "generation_pf": 0.9, "load": 1420, "load_pf": 0.9},
                {},
                {},
                {},
            ]
        },
    }


def test_get_schedule_data_interpolated_unsupported(test_client: TestClient, data_seed):
    # This tests shows the expected behavior when interpolating to an unsupported interval
    response = test_client.get(
        "/sce1/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.MIN_5.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": ["11KV"],
        },
    )
    assert response.status_code == 404
