from datetime import datetime
from typing import Dict, List, Optional, Set, Union

from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from idp_schedule_provider.forecaster import exceptions, resampler, schemas
from idp_schedule_provider.forecaster.models import EventData, Scenarios, ScheduleData


def insert_scenarios(db: Session, scenarios: List[Scenarios]) -> None:
    """
    This function exists for testing purposes only. It is used to seed the database with fake data
    """
    db.add_all(scenarios)
    db.flush()


def insert_schedules(db: Session, schedules: List[Union[ScheduleData, EventData]]) -> None:
    db.add_all(schedules)
    db.flush()


def get_all_scenarios(db: Session) -> schemas.GetScenariosResponseModel:
    return schemas.GetScenariosResponseModel.from_scenarios(db.query(Scenarios).all())


def get_asset_timespan(
    db: Session,
    scenario_id: schemas.ScenarioID,
    *,
    asset_name: Optional[str] = None,
    feeders: Optional[List[str]] = None,
) -> schemas.GetTimeSpanModel:
    try:
        db.query(Scenarios).filter(Scenarios.id == scenario_id).one()
    except NoResultFound:
        raise exceptions.ScenarioNotFoundException()

    query = db.query(
        func.min(ScheduleData.timestamp).label("min"),
        func.max(ScheduleData.timestamp).label("max"),
        ScheduleData.asset_name,
    ).filter(
        ScheduleData.scenario_id == scenario_id,
    )

    if asset_name is not None:
        query = query.filter(ScheduleData.asset_name == asset_name)

    if feeders:
        query = query.filter(ScheduleData.feeder.in_(feeders))

    return schemas.GetTimeSpanModel(
        assets={
            asset.asset_name: schemas.TimeSpanModel(
                start_datetime=asset.min, end_datetime=asset.max
            )
            for asset in query.group_by(ScheduleData.asset_name).all()
        }
    )


def get_event_timespan(
    db: Session,
    scenario_id: schemas.ScenarioID,
    *,
    asset_name: Optional[str] = None,
    feeders: Optional[List[str]] = None,
) -> schemas.GetTimeSpanModel:
    try:
        db.query(Scenarios).filter(Scenarios.id == scenario_id).one()
    except NoResultFound:
        raise exceptions.ScenarioNotFoundException()

    query = db.query(
        func.min(EventData.start_timestamp).label("min"),
        func.max(EventData.end_timestamp).label("max"),
        EventData.asset_name,
    ).filter(
        EventData.scenario_id == scenario_id,
    )

    if asset_name is not None:
        query = query.filter(EventData.asset_name == asset_name)

    if feeders:
        query = query.filter(EventData.feeder.in_(feeders))

    return schemas.GetTimeSpanModel(
        assets={
            asset.asset_name: schemas.TimeSpanModel(
                start_datetime=asset.min, end_datetime=asset.max
            )
            for asset in query.group_by(EventData.asset_name).all()
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
    *,
    asset_name: Optional[str] = None,
    feeders: Optional[List[str]] = None,
) -> schemas.GetSchedulesResponseModel:
    try:
        db.query(Scenarios).filter(Scenarios.id == scenario_id).one()
    except NoResultFound:
        raise exceptions.ScenarioNotFoundException()

    query = db.query(ScheduleData).filter(
        ScheduleData.scenario_id == scenario_id,
        ScheduleData.timestamp.between(start_time, end_time),
    )

    if asset_name is not None:
        query = query.filter(ScheduleData.asset_name == asset_name)

    if feeders:
        query = query.filter(ScheduleData.feeder.in_(feeders))

    query_data = query.order_by(ScheduleData.asset_name, ScheduleData.timestamp).all()
    response_data = _query_data_to_schedule_response(query_data, time_interval)
    return resampler.resample_data(
        time_interval, interpolation_method, sampling_modes, response_data
    )


def get_asset_events_data(
    db: Session,
    scenario_id: schemas.ScenarioID,
    start_time: datetime,
    end_time: datetime,
    *,
    asset_name: Optional[str] = None,
    feeders: Optional[List[str]] = None,
) -> schemas.GetEventsResponseModel:
    try:
        db.query(Scenarios).filter(Scenarios.id == scenario_id).one()
    except NoResultFound:
        raise exceptions.ScenarioNotFoundException()

    query = db.query(EventData).filter(
        EventData.scenario_id == scenario_id,
        or_(
            EventData.start_timestamp.between(start_time, end_time),
            EventData.end_timestamp.between(start_time, end_time),
        ),
    )

    if asset_name is not None:
        query = query.filter(EventData.asset_name == asset_name)

    if feeders is not None:
        query = query.filter(EventData.feeder.in_(feeders))

    query_data = query.order_by(EventData.start_timestamp).all()
    return _query_data_to_events_response(query_data)


def _query_data_to_schedule_response(
    query_data: List[ScheduleData],
    time_interval: schemas.TimeInterval,
) -> schemas.GetSchedulesResponseModel:
    asset_names: Set[str] = set()
    entries_by_time: Dict[datetime, Dict[str, ScheduleData]] = {}
    for entry in query_data:
        if entry.timestamp not in entries_by_time:
            entries_by_time[entry.timestamp] = {}

        entries_by_time[entry.timestamp][entry.asset_name] = entry
        asset_names.add(entry.asset_name)

    assets: Dict[schemas.AssetID, List[schemas.ScheduleEntry]] = {}
    for asset in asset_names:
        assets[asset] = []
        for entry_by_time in entries_by_time.values():
            try:
                value = entry_by_time[asset].data
            except (KeyError, AttributeError):
                value = {}
            assets[asset].append(value)

    return schemas.GetSchedulesResponseModel(
        time_interval=time_interval,
        time_stamps=sorted(entries_by_time.keys()),
        assets=assets,
    )


def _query_data_to_events_response(
    events_data: List[EventData],
) -> schemas.GetEventsResponseModel:
    assets: Dict[schemas.AssetID, List[schemas.EventsEntry]] = {}
    for event in events_data:
        asset_name = event.asset_name
        if asset_name not in assets:
            assets[asset_name] = []

        assets[asset_name].append(
            {
                "start_datetime": event.start_timestamp,
                "end_datetime": event.end_timestamp,
                **event.data,
            }
        )

    return schemas.GetEventsResponseModel(assets=assets)
