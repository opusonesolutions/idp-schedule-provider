import enum
from datetime import datetime, timezone
from typing import Any, Dict, Optional, cast

import sqlalchemy
from sqlalchemy import Column, ForeignKey, String, TypeDecorator
from sqlalchemy.orm import validates
from sqlalchemy.sql.sqltypes import JSON, DateTime, Integer

from idp_schedule_provider.forecaster.database import Base, engine


class EventType(enum.Enum):
    EV_CHARGING = "electric_vehicle_charge"
    CONTROL_MODE = "control_mode"


class UTCDateTime(TypeDecorator):
    """
    Database stores naive timezones which are assumed to be utc
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(  # type: ignore
        self, value: Optional[datetime], dialect
    ) -> Optional[datetime]:
        if value is not None:
            # force all datetimes to utc before persistance
            return value.astimezone(timezone.utc).replace(tzinfo=None)

        return None

    def process_result_value(self, value: Optional[datetime], *_) -> Optional[datetime]:
        if value is not None:
            # force all datetimes to utc on retrieval
            return datetime(
                value.year,
                value.month,
                value.day,
                value.hour,
                value.minute,
                value.second,
                value.microsecond,
                tzinfo=timezone.utc,
            )
        return None


class Scenarios(Base):
    __tablename__ = "scenarios"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String, nullable=True)


class ScheduleData(Base):
    __tablename__ = "schedule_data"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String, ForeignKey(Scenarios.id))
    asset_name = Column(String, index=True)
    feeder = Column(String, index=True)
    data = Column(cast("sqlalchemy.types.TypeEngine[Dict[str, Any]]", JSON()))  # force type to dict
    timestamp = Column(UTCDateTime, index=True)


class EventData(Base):
    __tablename__ = "event_data"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String, ForeignKey(Scenarios.id))
    asset_name = Column(String, index=True)
    feeder = Column(String, index=True)
    data = Column(cast("sqlalchemy.types.TypeEngine[Dict[str, Any]]", JSON()))  # force type to dict
    event_type = Column(String, index=True)
    start_timestamp = Column(UTCDateTime, index=True)
    end_timestamp = Column(UTCDateTime, index=True)

    @validates("event_type")
    def validate_event_type(self, key, event_type):
        if event_type is None:
            return None

        EventType(event_type)  # propagate value error if exists
        return event_type


Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
