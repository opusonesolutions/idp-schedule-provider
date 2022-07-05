from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union

from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from idp_schedule_provider.forecaster import exceptions, resampler, schemas
from idp_schedule_provider.forecaster.models import EventData, Scenarios, ScheduleData


def scenario_exists(db: Session, scenario_id: str):
    """check does scenario exist in schedule provider by id"""

    query = db.query(schemas.Scenarios).filter_by(id=scenario_id)

    return query.one_or_none()


def create_scenario(
    db: Session, scenario_id: schemas.ScenarioID, scenario_data: schemas.ScenarioModel
):
    """validate and create/update scenario db model"""
    if scenario_exists(db, scenario_id=scenario_id):
        db.query(schemas.Scenarios).filter_by(id=scenario_id).update(
            {"name": scenario_data.name, "description": scenario_data.description}
        )
    else:
        scenario_model = Scenarios(
            id=scenario_id, name=scenario_data.name, description=scenario_data.description
        )
        insert_rows(db, [scenario_model])


def delete_scenario(db: Session, scenario: schemas.ScenarioID) -> None:
    """Delete scenario and associated schedules & events in schedule provider."""

    db.query(EventData).filter_by(scenario_id=scenario).delete()
    db.query(ScheduleData).filter_by(scenario_id=scenario).delete()
    db.query(Scenarios).filter_by(id=scenario).delete()


def insert_rows(db: Session, rows: List[Union[ScheduleData, EventData, Scenarios]]) -> None:
    """insert data to database"""
    db.add_all(rows)
    db.flush()


def validate_schedules(schedules: schemas.AddNewSchedulesModel):
    timestamps = schedules.time_stamps
    asset_schedules = schedules.dict()["assets"]

    # validate asset schedules should have same length with timestamps
    if any([len(schedules) != len(timestamps) for _, schedules in asset_schedules.items()]):
        raise IndexError

    if len(timestamps) <= 1:
        return
    # validate timestamps interval, it should be 1 hour
    for idx in range(len(timestamps) - 1):
        if (timestamps[idx + 1] - timestamps[idx]) != timedelta(hours=1):
            raise exceptions.BadAssetScheduleTimeIntervalException


def add_schedules(
    db: Session,
    scenario: schemas.ScenarioID,
    feeder: schemas.FeederID,
    new_schedules: schemas.AddNewSchedulesModel,
) -> None:
    """Add new asset schedule to schedule provider"""
    if not scenario_exists(db, scenario_id=scenario):
        raise exceptions.ScenarioNotFoundException

    timestamps = new_schedules.time_stamps
    asset_schedules = new_schedules.dict()["assets"]
    new_schedule_models = []

    validate_schedules(new_schedules)

    query_data = (
        db.query(ScheduleData)
        .filter(
            ScheduleData.scenario_id == scenario,
            ScheduleData.timestamp.between(timestamps[0], timestamps[-1]),
            ScheduleData.feeder == feeder,
        )
        .all()
    )

    assets_with_schedules: Set[Tuple[str, datetime]] = set(
        [(schedule_data.asset_name, schedule_data.timestamp) for schedule_data in query_data]
    )

    for asset_id, schedules in asset_schedules.items():
        for idx, schedule in enumerate(schedules):

            timestamp = timestamps[idx]

            if (asset_id, timestamp) in assets_with_schedules:
                db.query(ScheduleData).filter_by(
                    scenario_id=scenario, timestamp=timestamp, asset_name=asset_id, feeder=feeder
                ).update({"data": schedule})
            else:
                new_schedule_models.append(
                    ScheduleData(
                        scenario_id=scenario,
                        asset_name=asset_id,
                        feeder=feeder,
                        data=schedule,
                        timestamp=timestamp,
                    )
                )

    insert_rows(db, new_schedule_models)


def add_events(
    db: Session,
    scenario: schemas.ScenarioID,
    feeder: schemas.FeederID,
    new_events: schemas.AddNewEventsModel,
) -> None:
    """Add new asset events to schedule provider"""
    if not scenario_exists(db, scenario_id=scenario):
        raise exceptions.ScenarioNotFoundException

    asset_events = new_events.dict()["assets"]
    new_event_models = []

    for asset_id, events in asset_events.items():
        for event in events:
            start_time, end_time = event.pop("start_datetime"), event.pop("end_datetime")
            new_event_models.append(
                EventData(
                    scenario_id=scenario,
                    asset_name=asset_id,
                    feeder=feeder,
                    data=event,
                    start_timestamp=start_time,
                    end_timestamp=end_time,
                )
            )
    insert_rows(db, new_event_models)


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
