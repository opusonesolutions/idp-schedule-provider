# tests for compliance of the asset schedules API
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from idp_schedule_provider.forecaster.controller import insert_rows
from idp_schedule_provider.forecaster.models import ScheduleData
from idp_schedule_provider.forecaster.schemas import (
    InterpolationMethod,
    SamplingMode,
    TimeInterval,
)


@pytest.fixture()
def feeder_seed():
    return ["20KV", "11KV"]


@pytest.fixture()
def cost_schedule_data_seed(database_client: Session, scenario_seed, feeder_seed):
    forecast_rows = []
    for i in range(1, 3):
        # add a switch with only a single timepoint
        forecast_rows.extend(
            [
                ScheduleData(
                    scenario_id=scenario_seed.id,
                    asset_name="Tap Changer 1",
                    feeder=feeder_seed[0],
                    data={
                        "tap_changer_cost": i,
                    },
                    timestamp=datetime(2000, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                ),
                ScheduleData(
                    scenario_id=scenario_seed.id,
                    asset_name="Capacitor 1",
                    feeder=feeder_seed[0],
                    data={
                        "capacitor_operation_cost": i,
                    },
                    timestamp=datetime(2000, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                ),
                ScheduleData(
                    scenario_id=scenario_seed.id,
                    asset_name="Battery 1",
                    feeder=feeder_seed[0],
                    data={
                        "active_energy_cost": i,
                    },
                    timestamp=datetime(2000, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                ),
                ScheduleData(
                    scenario_id=scenario_seed.id,
                    asset_name="Battery 2",
                    feeder=feeder_seed[0],
                    data={
                        "active_energy_cost": [{"x": 1, "y": i}, {"x": 1.5, "y": i + 0.5}],
                    },
                    timestamp=datetime(2000, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                ),
            ]
        )
    insert_rows(database_client, forecast_rows)


@pytest.fixture()
def data_seed(database_client: Session, scenario_seed, feeder_seed):
    forecast_rows = []
    # add a switch with only a single timepoint
    forecast_rows.append(
        ScheduleData(
            scenario_id=scenario_seed.id,
            asset_name="Switch 1",
            feeder=feeder_seed[0],
            data={
                "status": 1.0,
            },
            timestamp=datetime(2000, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
        )
    )
    # add 2 hr of feeder data
    for i in range(3):
        forecast_rows.append(
            ScheduleData(
                scenario_id=scenario_seed.id,
                asset_name=feeder_seed[1],
                feeder=feeder_seed[1],
                data={
                    "load": 1400 + i * 10,
                    "load_pf": 0.9,
                    "generation": 1600 - i * 10,
                    "generation_pf": 0.9,
                },
                timestamp=datetime(2000, 1, 1, i, 0, 0, tzinfo=timezone.utc),
            )
        )

    insert_rows(database_client, forecast_rows)


def test_get_timespan_missing_scenario(test_client: TestClient, feeder_seed):
    response = test_client.get(
        "/missing_scenario/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.HOUR_1.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": feeder_seed,
        },
    )
    assert response.status_code == 404


def test_get_timespan_none(test_client: TestClient, scenario_seed, feeder_seed):
    response = test_client.get(
        f"/{scenario_seed.id}/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.HOUR_1.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": feeder_seed,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "time_interval": TimeInterval.HOUR_1.value,
        "assets": {},
        "time_stamps": [],
    }


def test_get_schedule_data_hourly_by_feeder(
    test_client: TestClient, data_seed, scenario_seed, feeder_seed
):
    # as we are storing our data hourly, there is no interpolation/sampling applied
    response = test_client.get(
        f"/{scenario_seed.id}/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.HOUR_1.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": feeder_seed,
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


def test_get_schedule_data_hourly_by_asset(
    test_client: TestClient, data_seed, scenario_seed, feeder_seed
):
    # only get data within the specified timerange
    response = test_client.get(
        f"/{scenario_seed.id}/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.HOUR_1.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "asset_name": feeder_seed[1],
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


def test_get_schedule_data_datetime_filter(
    test_client: TestClient, scenario_seed, data_seed, feeder_seed
):
    feeder = feeder_seed[1]
    # only get data within the specified timerange
    response = test_client.get(
        f"/{scenario_seed.id}/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 1, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.HOUR_1.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": [feeder],
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "time_interval": TimeInterval.HOUR_1.value,
        "time_stamps": ["2000-01-01T01:00:00+00:00"],
        "assets": {
            feeder: [
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
def test_get_schedule_data_sampled(
    test_client: TestClient, interval: TimeInterval, data_seed, scenario_seed, feeder_seed
):
    # daily or higher implies sampling due to hourly data stored
    feeder = feeder_seed[1]
    response = test_client.get(
        f"/{scenario_seed.id}/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": interval.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.WEIGHTED_AVERAGE.value,
            "feeders": [feeder],
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "time_interval": interval.value,
        "time_stamps": ["2000-01-01T00:00:00+00:00"],
        "assets": {
            feeder: [
                {
                    "generation": 1590,
                    "generation_pf": 0.9,
                    "load": 1410,
                    "load_pf": 0.9,
                }
            ]
        },
    }


def test_get_schedule_data_sampled_unsupported(
    test_client: TestClient, scenario_seed, data_seed, feeder_seed
):
    feeder = feeder_seed[1]
    # This tests shows the expected behavior when sampling to an unsupported interval
    response = test_client.get(
        f"/{scenario_seed.id}/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.YEAR_1.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": feeder,
        },
    )
    assert response.status_code == 404


@pytest.mark.parametrize("interval", [TimeInterval.MIN_15])
def test_get_schedule_data_interpolated(
    test_client: TestClient,
    scenario_seed,
    data_seed,
    feeder_seed,
    interval,
):
    feeder = feeder_seed[1]
    # daily or higher implies sampling due to hourly data stored
    # 30 min intervel behavior should be the same aside from having half as many new datapoints
    response = test_client.get(
        f"/{scenario_seed.id}/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 2, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": interval.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": feeder,
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
            feeder: [
                {
                    "generation": 1590,
                    "generation_pf": 0.9,
                    "load": 1410,
                    "load_pf": 0.9,
                },
                {
                    "generation": 1587.5,
                    "generation_pf": 0.9,
                    "load": 1412.5,
                    "load_pf": 0.9,
                },
                {
                    "generation": 1585,
                    "generation_pf": 0.9,
                    "load": 1415,
                    "load_pf": 0.9,
                },
                {
                    "generation": 1582.5,
                    "generation_pf": 0.9,
                    "load": 1417.5,
                    "load_pf": 0.9,
                },
                {
                    "generation": 1580,
                    "generation_pf": 0.9,
                    "load": 1420,
                    "load_pf": 0.9,
                },
                {},
                {},
                {},
            ]
        },
    }


def test_get_schedule_data_interpolated_unsupported(
    test_client: TestClient, scenario_seed, data_seed, feeder_seed
):
    # This tests shows the expected behavior when interpolating to an unsupported interval
    response = test_client.get(
        f"/{scenario_seed.id}/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": TimeInterval.MIN_5.value,
            "interpolation_method": InterpolationMethod.LINEAR.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": feeder_seed[1],
        },
    )
    assert response.status_code == 404


@pytest.mark.parametrize(
    "interval, interpolation, expected",
    [
        (
            TimeInterval.HOUR_1,
            InterpolationMethod.LINEAR,
            {
                "time_interval": "1 hour",
                "time_stamps": ["2000-01-01T01:00:00+00:00", "2000-01-01T02:00:00+00:00"],
                "assets": {
                    "Battery 1": [
                        {"active_energy_cost": 1.0},
                        {"active_energy_cost": 2.0},
                    ],
                    "Battery 2": [
                        {"active_energy_cost": [{"x": 1.0, "y": 1.0}, {"x": 1.5, "y": 1.5}]},
                        {"active_energy_cost": [{"x": 1.0, "y": 2.0}, {"x": 1.5, "y": 2.5}]},
                    ],
                    "Tap Changer 1": [{"tap_changer_cost": 1.0}, {"tap_changer_cost": 2.0}],
                    "Capacitor 1": [
                        {"capacitor_operation_cost": 1.0},
                        {"capacitor_operation_cost": 2.0},
                    ],
                },
            },
        ),
        (
            TimeInterval.MIN_30,
            InterpolationMethod.LOCF,
            {
                "time_interval": "30 minutes",
                "time_stamps": [
                    "2000-01-01T01:00:00+00:00",
                    "2000-01-01T01:30:00+00:00",
                    "2000-01-01T02:00:00+00:00",
                    "2000-01-01T02:30:00+00:00",
                ],
                "assets": {
                    "Battery 1": [
                        {"active_energy_cost": 1.0},
                        {"active_energy_cost": 1.0},
                        {"active_energy_cost": 2.0},
                        {"active_energy_cost": 2.0},
                    ],
                    "Battery 2": [
                        {"active_energy_cost": [{"x": 1.0, "y": 1.0}, {"x": 1.5, "y": 1.5}]},
                        {"active_energy_cost": [{"x": 1.0, "y": 1.0}, {"x": 1.5, "y": 1.5}]},
                        {"active_energy_cost": [{"x": 1.0, "y": 2.0}, {"x": 1.5, "y": 2.5}]},
                        {"active_energy_cost": [{"x": 1.0, "y": 2.0}, {"x": 1.5, "y": 2.5}]},
                    ],
                    "Tap Changer 1": [
                        {"tap_changer_cost": 1.0},
                        {"tap_changer_cost": 1.0},
                        {"tap_changer_cost": 2.0},
                        {"tap_changer_cost": 2.0},
                    ],
                    "Capacitor 1": [
                        {"capacitor_operation_cost": 1.0},
                        {"capacitor_operation_cost": 1.0},
                        {"capacitor_operation_cost": 2.0},
                        {"capacitor_operation_cost": 2.0},
                    ],
                },
            },
        ),
        (
            TimeInterval.MIN_30,
            InterpolationMethod.LINEAR,
            {
                "time_interval": "30 minutes",
                "time_stamps": [
                    "2000-01-01T01:00:00+00:00",
                    "2000-01-01T01:30:00+00:00",
                    "2000-01-01T02:00:00+00:00",
                    "2000-01-01T02:30:00+00:00",
                ],
                "assets": {
                    "Battery 1": [
                        {"active_energy_cost": 1.0},
                        {"active_energy_cost": 1.5},
                        {"active_energy_cost": 2.0},
                        {},
                    ],
                    "Battery 2": [
                        {"active_energy_cost": [{"x": 1.0, "y": 1.0}, {"x": 1.5, "y": 1.5}]},
                        {"active_energy_cost": None},
                        {"active_energy_cost": [{"x": 1.0, "y": 2.0}, {"x": 1.5, "y": 2.5}]},
                        {},
                    ],
                    "Tap Changer 1": [
                        {"tap_changer_cost": 1.0},
                        {"tap_changer_cost": 1.5},
                        {"tap_changer_cost": 2.0},
                        {},
                    ],
                    "Capacitor 1": [
                        {"capacitor_operation_cost": 1.0},
                        {"capacitor_operation_cost": 1.5},
                        {"capacitor_operation_cost": 2.0},
                        {},
                    ],
                },
            },
        ),
    ],
)
def test_get_cost_schedule_data(
    test_client: TestClient,
    cost_schedule_data_seed,
    scenario_seed,
    feeder_seed,
    interval,
    interpolation,
    expected,
):
    response = test_client.get(
        f"/{scenario_seed.id}/asset_schedules",
        params={
            "start_datetime": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            "time_interval": interval.value,
            "interpolation_method": interpolation.value,
            "sampling_mode": SamplingMode.HOLD_FIRST.value,
            "feeders": feeder_seed[0],
        },
    )
    assert response.json() == expected
