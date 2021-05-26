from datetime import datetime
from typing import Dict, List, Optional, Set

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from idp_schedule_provider.forecaster import exceptions, resampler, schemas
from idp_schedule_provider.forecaster.models import ForecastData, Scenarios


def insert_scenarios(db: Session, scenarios: List[Scenarios]):
    """
    This function exists for testing purposes only. It is used to seed the database with fake data
    """
    db.add_all(scenarios)
    db.commit()


def insert_schedules(db: Session, schedules: List[ForecastData]):
    db.add_all(schedules)
    db.commit()


def get_all_scenarios(db: Session) -> schemas.GetScenariosResponseModel:
    return schemas.GetScenariosResponseModel.from_scenarios(db.query(Scenarios).all())


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

    entries_by_asset: Dict[schemas.AssetID, List[ForecastData]] = {}
    timestamps: Set[datetime] = set()
    for entry in query:
        if entry.asset_name not in entries_by_asset:
            entries_by_asset[entry.asset_name] = []

        asset_entry = entries_by_asset[entry.asset_name]
        asset_entry.append(entry)
        timestamps.add(entry.timestamp)

    response_data = schemas.GetSchedulesResponseModel(
        time_interval=time_interval,
        timestamps=sorted(timestamps),
        assets={asset: [val.data for val in values] for asset, values in entries_by_asset.items()},
    )

    return resampler.resample_data(
        time_interval, interpolation_method, sampling_modes, response_data
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

    entries_by_asset: Dict[schemas.AssetID, List[ForecastData]] = {}
    timestamps: Set[datetime] = set()
    for entry in query:
        if entry.asset_name not in entries_by_asset:
            entries_by_asset[entry.asset_name] = []

        asset_entry = entries_by_asset[entry.asset_name]
        asset_entry.append(entry)
        timestamps.add(entry.timestamp)

    response_data = schemas.GetSchedulesResponseModel(
        time_interval=time_interval,
        timestamps=sorted(timestamps),
        assets={asset: [val.data for val in values] for asset, values in entries_by_asset.items()},
    )

    return resampler.resample_data(
        time_interval, interpolation_method, sampling_modes, response_data
    )
