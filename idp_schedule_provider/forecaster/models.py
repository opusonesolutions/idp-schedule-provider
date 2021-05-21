from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.sql.sqltypes import JSON, DateTime, Integer

from idp_schedule_provider.forecaster.database import Base, engine


class Scenarios(Base):
    __tablename__ = "scenarios"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String, nullable=True)


class ForecastData(Base):
    __tablename__ = "forecast_data"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String, ForeignKey(Scenarios.id))
    asset_name = Column(String, index=True)
    feeder = Column(String, index=True)
    data = Column(JSON)
    timestamp = Column(DateTime(timezone=True))


Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
