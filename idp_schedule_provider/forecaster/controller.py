from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from idp_schedule_provider.forecaster import exceptions, schemas
from idp_schedule_provider.forecaster.models import ForecastData, Scenarios


def seed(db: Session):
    scenario1 = Scenarios(id="sce1", name="Scenario 1", description="Test Scenario 1")
    scenario2 = Scenarios(id="sce2", name="Scenario 2", description="Test Scenario 2")
    db.add(scenario1)
    db.add(scenario2)

    for asset, feeder, data in [
        ("asset_1", "f1", {"p": 25, "q": 0.5}),
        ("asset_2", "f2", {"p": {"A": 25}, "q": {"A": 0.5}}),
        ("asset_3", "f2", {"bla": 25, "blab": 0.5}),
    ]:
        for i in range(24):
            timestamp = datetime(2000, 1, 1, i, 0, 0, 0, timezone.utc)
            forecast_data = ForecastData(
                scenario_id="sce1", asset_name=asset, feeder=feeder, data=data, timestamp=timestamp
            )
            db.add(forecast_data)
            db.commit()


def get_all_scenarios(db: Session) -> schemas.GetScenariosSchema:
    return schemas.GetScenariosSchema.from_scenarios(db.query(Scenarios).all())


def get_asset_timespan(
    db: Session, scenario_id: schemas.ScenarioID, asset_name: str
) -> schemas.GetTimeSpanModel:
    try:
        db.query(Scenarios).filter(Scenarios.id == scenario_id).one()
    except NoResultFound:
        raise exceptions.ScenarioNotFoundException()

    query = db.query(
        func.min(ForecastData.timestamp).label("min"),
        func.max(ForecastData.timestamp).label("max"),
        ForecastData.asset_name,
    ).filter(
        ForecastData.asset_name == asset_name,
        ForecastData.scenario_id == scenario_id,
    )

    return schemas.GetTimeSpanModel(
        assets={
            asset.asset_name: schemas.TimeSpanModel(
                start_datetime=asset.min, end_datetime=asset.max
            )
            for asset in query.group_by(ForecastData.asset_name).all()
        }
    )


def get_scenario_timespan(
    db: Session, scenario_id: schemas.ScenarioID, feeders: Optional[List[str]]
) -> schemas.GetTimeSpanModel:
    try:
        db.query(Scenarios).filter(Scenarios.id == scenario_id).one()
    except NoResultFound:
        raise exceptions.ScenarioNotFoundException()

    query = db.query(
        func.min(ForecastData.timestamp).label("min"),
        func.max(ForecastData.timestamp).label("max"),
        ForecastData.asset_name,
    ).filter(
        ForecastData.scenario_id == scenario_id,
    )
    if feeders:
        query = query.filter(ForecastData.feeder.in_(feeders))

    return schemas.GetTimeSpanModel(
        assets={
            asset.asset_name: schemas.TimeSpanModel(
                start_datetime=asset.min, end_datetime=asset.max
            )
            for asset in query.group_by(ForecastData.asset_name).all()
        }
    )


def get_asset_data(
    db: Session,
    scenario_id: schemas.ScenarioID,
    start_time: datetime,
    end_time: datetime,
    time_interval: schemas.TimeInterval,
    interpolation_method: schemas.InterpolationMethod,
    sampling_modes: schemas.SamplingMode,
    asset_name: str,
) -> schemas.GetSchedulesResponseModel:
    try:
        db.query(Scenarios).filter(Scenarios.id == scenario_id).one()
    except NoResultFound:
        raise exceptions.ScenarioNotFoundException()

    query = (
        db.query(ForecastData)
        .filter(
            ForecastData.scenario_id == scenario_id,
            ForecastData.timestamp.between(start_time, end_time),
            ForecastData.asset_name == asset_name,
        )
        .order_by(ForecastData.asset_name, ForecastData.timestamp)
    ).all()

    return _resample_data(
        start_time, end_time, time_interval, interpolation_method, sampling_modes, query
    )


def get_scenario_data(
    db: Session,
    scenario_id: schemas.ScenarioID,
    start_time: datetime,
    end_time: datetime,
    time_interval: schemas.TimeInterval,
    interpolation_method: schemas.InterpolationMethod,
    sampling_modes: schemas.SamplingMode,
    feeders: List[str],
) -> schemas.GetSchedulesResponseModel:
    try:
        db.query(Scenarios).filter(Scenarios.id == scenario_id).one()
    except NoResultFound:
        raise exceptions.ScenarioNotFoundException()

    query = (
        db.query(ForecastData)
        .filter(
            ForecastData.scenario_id == scenario_id,
            ForecastData.timestamp.between(start_time, end_time),
            ForecastData.feeder.in_(feeders),
        )
        .order_by(ForecastData.asset_name, ForecastData.timestamp)
        .all()
    )

    return _resample_data(
        start_time, end_time, time_interval, interpolation_method, sampling_modes, query
    )


def _resample_data(
    start: datetime,
    end: datetime,
    time_interval: schemas.TimeInterval,
    interpolation_method: schemas.InterpolationMethod,
    sampling_mode: schemas.SamplingMode,
    query_data: List[ForecastData],
) -> schemas.GetSchedulesResponseModel:
    """
    Basic data resampling

    ## Warning
    This implementation makes many assumptions which are probably not true about real data
    and is therefore *not* production ready.

    - stored data is evenly sampled at *hourly* intervals
    - no discrete variables are supported (eg. OPEN/CLOSED state of switches)
    """

    # TODO: Actually resample the data
    entries_by_asset: Dict[schemas.AssetID, List[ForecastData]] = {}
    timestamps: Set[datetime] = set()
    for entry in query_data:
        if entry.asset_name not in entries_by_asset:
            entries_by_asset[entry.asset_name] = []

        asset_entry = entries_by_asset[entry.asset_name]
        asset_entry.append(entry)
        timestamps.add(entry.timestamp)

    return schemas.GetSchedulesResponseModel(
        time_interval=time_interval,
        timestamps=sorted(timestamps),
        assets={asset: [val.data for val in values] for asset, values in entries_by_asset.items()},
    )
