from datetime import datetime, timezone
from typing import Dict, List

from idp_schedule_provider import models
from idp_schedule_provider.exceptions import ScenarioNotFoundException

SCENARIOS: Dict[models.ScenarioID, models.ScenarioModel] = {
    "012443-54543535-345345": models.ScenarioModel(name="test1", description="I be testin'"),
    "012345-54523532532-543": models.ScenarioModel(name="test2", description="I be testin' more"),
}


def get_all_scenarios() -> models.GetScenariosModel:
    return models.GetScenariosModel(scenarios=SCENARIOS)


def get_scenario_timespan(scenario: models.ScenarioID) -> models.GetTimeSpanModel:
    if scenario not in SCENARIOS:
        raise ScenarioNotFoundException()

    data = {}
    if scenario == "012443-54543535-345345":
        data = {
            "assets": {
                "asset_1": {
                    "start_date": "2000-01-01T00:00:00Z",
                    "end_date": "2000-12-31T23:59:59Z",
                },
                "asset_2": {
                    "start_date": "2010-01-01T00:00:00Z",
                    "end_date": "2000-12-31T23:59:59Z",
                },
            }
        }
    elif scenario == "012345-54523532532-543":
        data = {
            "assets": {
                "asset_1": {
                    "start_date": "2000-01-01T00:00:00Z",
                    "end_date": "2000-01-31T23:59:59Z",
                },
                "asset_2": {
                    "start_date": "2000-01-01T00:00:00Z",
                    "end_date": "2000-01-31T23:59:59Z",
                },
                "asset_3": {
                    "start_date": "2000-01-01T00:00:00Z",
                    "end_date": "2000-01-31T23:59:59Z",
                },
            }
        }

    return models.GetTimeSpanModel.parse_obj(data)


def get_asset_data(
    scenario: models.ScenarioID,
    start_time: datetime,
    end_time: datetime,
    time_interval: models.TimeInterval,
    interpolation_method: models.InterpolationMethod,
    sampling_modes: models.SamplingMode,
    asset_name: str,
) -> models.GetSchedulesResponseModel:
    if scenario not in SCENARIOS:
        raise ScenarioNotFoundException()

    data = {}
    if scenario == "012443-54543535-345345":
        data = {
            "time_interval": models.TimeInterval.YEAR_1,
            "timestamps": [datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc)],
            "assets": {
                "asset_1": [{"name": "p", "value": 45}],
                "asset_2": {
                    "A": [None],
                    "B": [{"name": "p", "value": 25}],
                    "C": [{"name": "q", "value": 15}],
                },
                "asset_ev": [
                    {
                        "value": 25,
                        "charge_event_start": datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc),
                        "charge_event_end": datetime(2000, 1, 2, 0, 0, 0, 0, timezone.utc),
                    }
                ],
            },
        }

    return models.GetSchedulesResponseModel.parse_obj(data)


def get_scenario_data(
    scenario: models.ScenarioID,
    start_time: datetime,
    end_time: datetime,
    time_interval: models.TimeInterval,
    interpolation_method: models.InterpolationMethod,
    sampling_modes: models.SamplingMode,
    feeders: List[str],
) -> models.GetSchedulesResponseModel:
    if scenario not in SCENARIOS:
        raise ScenarioNotFoundException()

    data = {}
    if scenario == "012443-54543535-345345":
        data = {
            "time_interval": models.TimeInterval.YEAR_1,
            "timestamps": [datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc)],
            "assets": {
                "asset_1": [{"name": "p", "value": 45}],
                "asset_2": {
                    "A": [None],
                    "B": [{"name": "p", "value": 25}],
                    "C": [{"name": "q", "value": 15}],
                },
                "asset_ev": [
                    {
                        "value": 25,
                        "charge_event_start": datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc),
                        "charge_event_end": datetime(2000, 1, 2, 0, 0, 0, 0, timezone.utc),
                    }
                ],
            },
        }

    return models.GetSchedulesResponseModel.parse_obj(data)
