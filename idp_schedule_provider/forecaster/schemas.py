from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from idp_schedule_provider.forecaster.models import Scenarios

AssetID = str
ScenarioID = str


class ScenarioModel(BaseModel):
    name: str
    description: Optional[str] = None


class GetScenariosSchema(BaseModel):
    scenarios: Dict[ScenarioID, ScenarioModel]

    class Config:
        schema_extra = {
            "example": {
                "scenarios": {
                    "012443-54543535-345345": ScenarioModel(
                        name="test1", description="I be testin'"
                    ),
                    "012345-54523532532-543": ScenarioModel(
                        name="test2", description="I be testin' more"
                    ),
                }
            }
        }

    @staticmethod
    def from_scenarios(scenarios: List[Scenarios]):
        return GetScenariosSchema(
            scenarios={
                scenario.id: ScenarioModel(name=scenario.name, description=scenario.description)
                for scenario in scenarios
            }
        )


class TimeSpanModel(BaseModel):
    start_datetime: datetime
    end_datetime: datetime


class GetTimeSpanModel(BaseModel):
    assets: Dict[AssetID, TimeSpanModel]

    class Config:
        schema_extra = {
            "example": {
                "assets": {
                    "asset_1": TimeSpanModel(
                        start_datetime=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc),
                        end_datetime=datetime(2000, 12, 31, 23, 59, 59, 999999, timezone.utc),
                    ),
                    "asset_2": TimeSpanModel(
                        start_datetime=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc),
                        end_datetime=datetime(2001, 12, 31, 23, 59, 59, 999999, timezone.utc),
                    ),
                }
            }
        }


VariableName = str
ScheduleValue = Optional[float]


class UnbalancedScheduleValue(BaseModel):
    A: ScheduleValue
    B: ScheduleValue
    C: ScheduleValue


ScheduleEntry = Dict[VariableName, Union[ScheduleValue, UnbalancedScheduleValue]]


class TimeInterval(str, Enum):
    MIN_5 = "5 minutes"
    MIN_15 = "15 minutes"
    MIN_30 = "30 minutes"
    HOUR_1 = "1 hour"
    DAY_1 = "1 day"
    MONTH_1 = "1 month"
    YEAR_1 = "1 year"


class InterpolationMethod(str, Enum):
    LINEAR = "linear"
    NOCB = "next_observation_carried_backward"
    LOCF = "last_observation_carried_forward"


class SamplingMode(str, Enum):
    WEIGHTED_AVERAGE = "weighted_average"
    HOLD_FIRST = "hold_first_value"


class GetSchedulesResponseModel(BaseModel):
    time_interval: TimeInterval
    timestamps: List[datetime]
    assets: Dict[AssetID, List[ScheduleEntry]]

    class Config:
        schema_extra = {
            "example": {
                "time_interval": TimeInterval.DAY_1,
                "timestamps": [
                    datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc),
                    datetime(2000, 1, 2, 0, 0, 0, 0, timezone.utc),
                ],
                "assets": {"asset_1": "TBD"},
            }
        }
