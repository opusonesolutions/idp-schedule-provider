from datetime import datetime, timezone
from enum import Enum
from typing import List, MutableMapping, Optional, Union

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel

from idp_schedule_provider.forecaster.models import Scenarios

AssetID = str
ScenarioID = str


class ScenarioModel(BaseModel):
    name: str
    description: Optional[str] = None


class GetScenariosResponseModel(BaseModel):
    scenarios: MutableMapping[ScenarioID, ScenarioModel]

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
        return GetScenariosResponseModel(
            scenarios={
                scenario.id: ScenarioModel(name=scenario.name, description=scenario.description)
                for scenario in scenarios
            }
        )


class TimeSpanModel(BaseModel):
    start_datetime: datetime
    end_datetime: datetime


class GetTimeSpanModel(BaseModel):
    assets: MutableMapping[AssetID, TimeSpanModel]

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


ScheduleEntry = MutableMapping[VariableName, Union[ScheduleValue, UnbalancedScheduleValue]]


class TimeInterval(Enum):
    # ensure entries are sorted smallest to largest
    MIN_5 = "5 minutes"
    MIN_15 = "15 minutes"
    MIN_30 = "30 minutes"
    HOUR_1 = "1 hour"
    DAY_1 = "1 day"
    MONTH_1 = "1 month"
    YEAR_1 = "1 year"

    def __gt__(self, other: "TimeInterval"):
        agg_order = [item for item in TimeInterval]
        return agg_order.index(self) > agg_order.index(other)

    def __ge__(self, other: "TimeInterval"):
        return self is other or self > other

    def get_delta(self) -> relativedelta:
        if self == TimeInterval.MIN_5:
            return relativedelta(minutes=5)
        if self == TimeInterval.MIN_15:
            return relativedelta(minutes=15)
        if self == TimeInterval.MIN_30:
            return relativedelta(minutes=30)
        if self == TimeInterval.HOUR_1:
            return relativedelta(hours=1)
        if self == TimeInterval.DAY_1:
            return relativedelta(days=1)
        if self == TimeInterval.MONTH_1:
            return relativedelta(months=1)
        if self == TimeInterval.YEAR_1:
            return relativedelta(years=1)
        raise NotImplementedError("Specified interval is not implemented")


class InterpolationMethod(Enum):
    LINEAR = "linear"
    NOCB = "next_observation_carried_backward"
    LOCF = "last_observation_carried_forward"


class SamplingMode(Enum):
    WEIGHTED_AVERAGE = "weighted_average"
    HOLD_FIRST = "hold_first_value"


class GetSchedulesResponseModel(BaseModel):
    time_interval: TimeInterval
    time_stamps: List[datetime]
    assets: MutableMapping[AssetID, List[ScheduleEntry]]

    class Config:
        schema_extra = {
            "example": {
                "time_interval": TimeInterval.DAY_1,
                "time_stamps": [
                    datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc),
                    datetime(2000, 1, 2, 0, 0, 0, 0, timezone.utc),
                ],
                "assets": {
                    "feeder_1": [
                        {
                            "load": 450000,
                            "load_pf": 0.9,
                            "generation": 45000,
                            "generation_pf": 0.95,
                        },
                        {
                            "load": 550000,
                            "load_pf": 0.86,
                            "generation": 75000,
                            "generation_pf": 0.95,
                        },
                    ],
                    "asset_2": [
                        {
                            "p": {"A": 24000, "B": 16000, "C": 20000},
                            "q": {"A": 4000, "B": 2000, "C": 3000},
                        },
                        None,
                    ],
                },
            }
        }
