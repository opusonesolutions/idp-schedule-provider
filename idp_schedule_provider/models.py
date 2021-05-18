from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

AssetID = str
ScenarioID = str


class ScenarioModel(BaseModel):
    name: str
    description: Optional[str] = None


class GetScenariosModel(BaseModel):
    scenarios: Dict[ScenarioID, ScenarioModel]


class TimeSpanModel(BaseModel):
    start_date: datetime
    end_date: datetime


class GetTimeSpanModel(BaseModel):
    assets: Dict[AssetID, TimeSpanModel]


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
    assets: Dict[
        AssetID,
        Union[List[Optional[ScheduleValue]], UnbalancedAssetModel, List[Optional[EVModel]]],
    ]
