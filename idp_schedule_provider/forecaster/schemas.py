from datetime import datetime, timezone
from enum import Enum
from typing import List, MutableMapping, Optional, Union

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field

from idp_schedule_provider.forecaster.models import Scenarios

AssetID = str
ScenarioID = str
FeederID = str


class ScenarioModel(BaseModel):
    name: str = Field(description="A short name describing the scenario")
    description: Optional[str] = Field(
        default=None, description="A longer description of the scenario"
    )


class GetScenariosResponseModel(BaseModel):
    scenarios: MutableMapping[ScenarioID, ScenarioModel] = Field(
        description="A mapping of scenarios that are available to be used"
    )

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
    def from_scenarios(scenarios: List[Scenarios]) -> "GetScenariosResponseModel":
        return GetScenariosResponseModel(
            scenarios={
                scenario.id: ScenarioModel(name=scenario.name, description=scenario.description)
                for scenario in scenarios
            }
        )


class TimeSpanModel(BaseModel):
    start_datetime: datetime = Field(
        description="A UTC ISO8601 timestamp which represents the first datapoint available"
    )
    end_datetime: datetime = Field(
        description="A UTC ISO8601 timestamp which represents the last datapoint available"
    )


class GetTimeSpanModel(BaseModel):
    assets: MutableMapping[AssetID, TimeSpanModel] = Field(
        description=(
            "A mapping of assets for which there is data available"
            "and the timespans where that data is available"
        )
    )

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
BalancedScheduleValue = Optional[float]
# Order of this is how parsing is attempted
EventsValue = Optional[Union[float, datetime]]


class UnbalancedScheduleValue(BaseModel):
    A: BalancedScheduleValue
    B: BalancedScheduleValue
    C: BalancedScheduleValue


class CostScheduleValue(BaseModel):
    x: float
    y: float


# order matters
ScheduleValue = Union[
    BalancedScheduleValue,
    List[CostScheduleValue],
    UnbalancedScheduleValue,
]

ScheduleEntry = MutableMapping[VariableName, ScheduleValue]
EventsEntry = MutableMapping[VariableName, EventsValue]


class TimeInterval(Enum):
    # ensure entries are sorted smallest to largest
    MIN_5 = "5 minutes"
    MIN_15 = "15 minutes"
    MIN_30 = "30 minutes"
    HOUR_1 = "1 hour"
    DAY_1 = "1 day"
    MONTH_1 = "1 month"
    YEAR_1 = "1 year"

    def __gt__(self, other: "TimeInterval") -> bool:
        agg_order = [item for item in TimeInterval]
        return agg_order.index(self) > agg_order.index(other)

    def __ge__(self, other: "TimeInterval") -> bool:
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


class AddNewSchedulesModel(BaseModel):
    time_stamps: List[datetime] = Field(
        description=(
            "A list of UTC ISO8601 timestamps (sorted ascending) "
            "for which data is available in the assets mapping"
        )
    )
    assets: MutableMapping[AssetID, List[ScheduleEntry]] = Field(
        description="A mapping of assets to their schedule data"
    )

    class Config:
        schema_extra = {
            "example": {
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
                        {
                            "p": {"A": 24000, "B": 16000, "C": 20000},
                            "q": {"A": 4000, "B": 2000, "C": 3000},
                        },
                    ],
                },
            }
        }


class GetSchedulesResponseModel(AddNewSchedulesModel):
    time_interval: TimeInterval = Field(
        description="The interval at which the schedule data is spaced"
    )

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
                            "active_energy_cost": [
                                {"x": 100, "y": 100.00},
                                {"x": 200, "y": 200.00},
                            ],
                        },
                        None,
                    ],
                },
            }
        }


class AddNewEventsModel(BaseModel):
    assets: MutableMapping[AssetID, List[EventsEntry]] = Field(
        description="A mapping of global evto their schedule data"
    )

    class Config:
        schema_extra = {
            "example": {
                "assets": {
                    "EV": [
                        {
                            "start_datetime": datetime(2000, 1, 1, 14, 0, 0, 0, timezone.utc),
                            "end_datetime": datetime(2000, 1, 1, 17, 0, 0, 0, timezone.utc),
                            "pf": 0.9,
                            "p_max": 2400,
                            "start_soc": 75,
                            "total_battery_capacity": 10000,
                        }
                    ],
                },
            }
        }


class GetEventsResponseModel(AddNewEventsModel):
    ...
