from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

AssetID = str
ScenarioID = str


class ScenarioModel(BaseModel):
    name: str
    description: Optional[str] = None


class GetScenariosModel(BaseModel):
    scenarios: Dict[ScenarioID, ScenarioModel]


@app.get("/scenario", response_model=GetScenariosModel)
async def get_scenarios():
    return GetScenariosModel.parse_obj(
        {
            "scenarios": {
                "012443-54543535-345345": {"name": "test1", "description": "I be testing"},
                "012345-54523532532-543524535": {
                    "name": "test2",
                    "description": "I be testing more",
                },
            }
        }
    )


class TimeSpanModel(BaseModel):
    start_date: datetime
    end_date: datetime


class GetTimeSpanModel(BaseModel):
    assets: Dict[AssetID, TimeSpanModel]


@app.get("/{scenario}/asset_schedules/timespan", response_model=GetTimeSpanModel)
async def get_schedule_timespans(scenario: ScenarioID):
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
    elif scenario == "012345-54523532532-543524535":
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
    else:
        raise HTTPException(404, "Scenario not found")

    return GetTimeSpanModel.parse_obj(data)


class ScheduleValue(BaseModel):
    name: str
    value: float


class UnbalancedAssetModel(BaseModel):
    A: List[Optional[ScheduleValue]]
    B: List[Optional[ScheduleValue]]
    C: List[Optional[ScheduleValue]]


class EVModel(BaseModel):
    value: float
    charge_event_start: datetime
    charge_event_end: datetime


class TimeInterval(str, Enum):
    MIN_5 = "5 minutes"
    MIN_15 = "15 minutes"
    MIN_30 = "30 minutes"
    HOUR_1 = "1 hour"
    DAY_1 = "1 day"
    MONTH_1 = "1 month"
    YEAR_1 = "1 year"


class GetSchedulesResponseModel(BaseModel):
    time_interval: TimeInterval
    timestamps: List[datetime]
    assets: Dict[
        AssetID,
        Union[List[Optional[ScheduleValue]], UnbalancedAssetModel, List[Optional[EVModel]]],
    ]


@app.get("/{scenario}/asset_schedules", response_model=GetSchedulesResponseModel)
async def get_schedules(scenario: ScenarioID):
    data = {}
    if scenario == "012443-54543535-345345":
        data = {
            "time_interval": TimeInterval.YEAR_1,
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
    else:
        raise HTTPException(404, "Scenario not found")

    return GetSchedulesResponseModel.parse_obj(data)
