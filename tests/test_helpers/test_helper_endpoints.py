from datetime import datetime, timezone

import pytest

from idp_schedule_provider.forecaster.schemas import (
    InterpolationMethod,
    SamplingMode,
    TimeInterval,
)


@pytest.mark.parametrize(
    "scenario_config, status_code",
    [
        ({"name": "test1", "description": "test1"}, 200),
        ({"name": "test2"}, 200),
    ],
)
def test_create_and_delete_scenario(test_client, scenario_config, status_code):
    scenario_id = "sce1"
    rsp = test_client.put(f"/scenario/{scenario_id}", json=scenario_config)

    assert rsp.status_code == status_code

    scenarios = test_client.get("/scenarios").json()
    assert scenarios["scenarios"][scenario_id]["name"] == scenario_config["name"]
    assert scenarios["scenarios"][scenario_id]["description"] == scenario_config.get(
        "description", None
    )

    rsp = test_client.delete(f"/scenario/{scenario_id}")
    assert rsp.ok
    all_scenarios = test_client.get("/scenarios").json()
    assert scenario_id not in all_scenarios["scenarios"]


def test_update_scenario_name(test_client):
    scenario_id = "test_scenario"
    scenario_1 = {"name": "test_1", "description": "test1"}
    scenario_2 = {"name": "test_2", "description": "test2"}

    rsp_1 = test_client.put(f"/scenario/{scenario_id}", json=scenario_1)
    assert rsp_1.status_code == 200
    all_scenarios = test_client.get("/scenarios").json()
    assert scenario_id in all_scenarios["scenarios"]
    assert all_scenarios["scenarios"][scenario_id] == scenario_1

    rsp_2 = test_client.put(f"/scenario/{scenario_id}", json=scenario_2)
    assert rsp_2.status_code == 200
    all_scenarios = test_client.get("/scenarios").json()
    assert scenario_id in all_scenarios["scenarios"]
    assert all_scenarios["scenarios"][scenario_id] == scenario_2


def test_delete_non_existent_scenario(test_client):
    rsp = test_client.delete("/scenario/hellow")
    assert rsp.ok


def test_add_and_update_schedule(test_client, scenario_seed):
    data = {
        "time_stamps": [
            "2000-01-01T01:00:00+00:00",
            "2000-01-01T02:00:00+00:00",
            "2000-01-01T03:00:00+00:00",
        ],
        "assets": {
            "feeder1": [
                {"generation": 1590.0, "generation_pf": 0.9, "load": 1410.0, "load_pf": 0.9},
                {"generation": 1587.5, "generation_pf": 0.9, "load": 1412.5, "load_pf": 0.9},
                {},
            ],
            "load_1": [{"p": 100.0, "q": 50.0}, {}, {"p": 500.0, "q": 40.0}],
        },
    }
    rsp = test_client.post("/sce1/asset_schedules/feeder1", json=data)
    assert rsp.status_code == 201

    params = {
        "start_datetime": datetime(2000, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
        "end_datetime": datetime(2000, 1, 1, 2, 59, 59, 999999, tzinfo=timezone.utc),
        "time_interval": TimeInterval.HOUR_1.value,
        "interpolation_method": InterpolationMethod.LINEAR.value,
        "sampling_mode": SamplingMode.HOLD_FIRST.value,
        "feeders": ["feeder1"],
    }
    response = test_client.get(
        "/sce1/asset_schedules",
        params=params,
    )

    assert response.json() == {
        "time_interval": TimeInterval.HOUR_1.value,
        "time_stamps": [
            "2000-01-01T01:00:00+00:00",
            "2000-01-01T02:00:00+00:00",
        ],
        "assets": {
            "feeder1": [
                {"generation": 1590.0, "generation_pf": 0.9, "load": 1410.0, "load_pf": 0.9},
                {"generation": 1587.5, "generation_pf": 0.9, "load": 1412.5, "load_pf": 0.9},
            ],
            "load_1": [{"p": 100.0, "q": 50.0}, {}],
        },
    }

    # update load 1 schedule
    data["assets"]["load_1"][1].update({"p": 1500.0, "q": 400.0})

    rsp = test_client.post("/sce1/asset_schedules/feeder1", json=data)
    assert rsp.status_code == 201

    response_data = test_client.get(
        "/sce1/asset_schedules",
        params=params,
    ).json()

    assert response_data["assets"]["load_1"][1] == {"p": 1500.0, "q": 400.0}


def test_add_event(test_client, scenario_seed):
    events = {
        "assets": {
            "EV1": [
                {
                    "pf": 0.9,
                    "p_max": 2400,
                    "start_soc": 75,
                    "total_battery_capacity": 10000,
                    "start_datetime": datetime(2000, 1, 1, 14, 0, 0, 0, timezone.utc).isoformat(),
                    "end_datetime": datetime(2000, 1, 1, 17, 59, 59, 59, timezone.utc).isoformat(),
                    "event_type": "electric_vehicle_charge",
                },
                {
                    "pf": 0.9,
                    "p_max": 2400,
                    "start_soc": 75,
                    "total_battery_capacity": 10000,
                    "start_datetime": datetime(2000, 1, 1, 23, 0, 0, 0, timezone.utc).isoformat(),
                    "end_datetime": datetime(2000, 1, 1, 23, 59, 59, 59, timezone.utc).isoformat(),
                    "event_type": "electric_vehicle_charge",
                },
            ],
            "EV2": [
                {
                    "pf": 0.9,
                    "p_max": 2400,
                    "start_soc": 75,
                    "total_battery_capacity": 10000,
                    "start_datetime": datetime(2000, 1, 1, 14, 0, 0, 0, timezone.utc).isoformat(),
                    "end_datetime": datetime(2000, 1, 1, 17, 59, 59, 59, timezone.utc).isoformat(),
                    "event_type": "electric_vehicle_charge",
                },
                {
                    "start_datetime": datetime(2000, 1, 1, 14, 0, 0, 0, timezone.utc).isoformat(),
                    "end_datetime": datetime(2000, 1, 1, 17, 59, 59, 59, timezone.utc).isoformat(),
                    "event_type": "control_mode",
                    "control_mode": "global",
                },
            ],
        }
    }

    rsp = test_client.post("/sce1/asset_events/test_ev", json=events)

    assert rsp.ok
    assert rsp.status_code == 201

    response = test_client.get(
        "/sce1/asset_events",
        params={
            "start_datetime": datetime(2000, 1, 1, 14, 0, 0, 0, timezone.utc).isoformat(),
            "end_datetime": datetime(2000, 1, 1, 17, 59, 59, 59, timezone.utc).isoformat(),
            "feeders": ["test_ev"],
        },
    )
    assert response.ok
    assert response.json()["assets"]["EV1"] == [
        {
            "pf": 0.9,
            "p_max": 2400,
            "start_soc": 75,
            "total_battery_capacity": 10000,
            "start_datetime": datetime(2000, 1, 1, 14, 0, 0, 0, timezone.utc).isoformat(),
            "end_datetime": datetime(2000, 1, 1, 17, 59, 59, 59, timezone.utc).isoformat(),
            "event_type": "electric_vehicle_charge",
        }
    ]
