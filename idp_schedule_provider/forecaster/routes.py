from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import Response
from sqlalchemy.orm.session import Session

from idp_schedule_provider.authentication.auth import validate_token
from idp_schedule_provider.forecaster import controller as forecast_controller
from idp_schedule_provider.forecaster import exceptions, schemas
from idp_schedule_provider.forecaster.database import get_db_session
from idp_schedule_provider.forecaster.resources import load_resource
from idp_schedule_provider.forecaster.seed_data import DUMMY_SOURCE, IEEE123_SOURCE

router = APIRouter()


@router.post(
    "/seed_data",
    tags=["test-only"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def seed_db(db: Session = Depends(get_db_session)):
    """
    Seeds the database with test data.

    ## Use Case
    This exists for testing purposes only. It is not part of the external schedule implementation
    and does not need to be implemented as part of the specification.
    """
    forecast_controller.insert_rows(db, DUMMY_SOURCE.scenarios)
    forecast_controller.insert_rows(db, DUMMY_SOURCE.forecast_data)
    forecast_controller.insert_rows(db, IEEE123_SOURCE.scenarios)
    forecast_controller.insert_rows(db, IEEE123_SOURCE.forecast_data)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/scenario/{scenario}",
    tags=["test-only"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_scenario(
    scenario: schemas.ScenarioID,
    scenario_data: schemas.ScenarioModel,
    _: bool = Depends(validate_token),
    db: Session = Depends(get_db_session),
):
    """
    Create or update scenario information in schedule provider. If scenario id does not exist,
    schedule provider will create new scenario; if scenario id exists, schedule provider will
    update scenario information base on payload.

    ## Use Case
    This exists for testing purposes only. It is not part of the external schedule implementation
    and does not need to be implemented as part of the specification.
    """
    try:
        forecast_controller.create_or_update_scenario(db, scenario, scenario_data)
    except exceptions.DuplicateScenarioNameException as e:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Scenario name `{scenario_data.name}` is already found",
        ) from e
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to update scenario"
        ) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/scenario/{scenario}",
    tags=["test-only"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_scenario(
    scenario: schemas.ScenarioID,
    _: bool = Depends(validate_token),
    db: Session = Depends(get_db_session),
):
    """
    Delete scenario and associated schedules & events in schedule provider.

    ## Use Case
    This exists for testing purposes only. It is not part of the external schedule implementation
    and does not need to be implemented as part of the specification.
    """

    try:
        forecast_controller.delete_scenario(db, scenario)
    except exceptions.ScenarioNotFoundException as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Scenario `{scenario}` not found") from e
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to delete scenario"
        ) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/scenarios",
    response_model=schemas.GetScenariosResponseModel,
    description=load_resource("scenarios_response"),
    tags=["spec-required"],
)
async def get_scenarios(
    _: bool = Depends(validate_token), db: Session = Depends(get_db_session)
) -> schemas.GetScenariosResponseModel:
    """
    Gets all scenarios currently available from the schedule provider.
    """
    return forecast_controller.get_all_scenarios(db)


@router.get(
    "/{scenario}/asset_schedules/timespan",
    response_model=schemas.GetTimeSpanModel,
    description=load_resource("timespan_response"),
    tags=["spec-required"],
)
async def get_schedule_timespans(
    scenario: schemas.ScenarioID = Path(
        ...,
        description=(
            "The id of the scenario to get data for. This must be an **exact** "
            "match to an ID returned from the /scenarios API."
        ),
    ),
    feeders: Optional[List[str]] = Query(
        None, description="The feeders for which the asset data should be retrieved."
    ),
    asset_name: Optional[str] = Query(
        None, description="The name of the asset for which the asset data should be retrieved."
    ),
    _: bool = Depends(validate_token),
    db: Session = Depends(get_db_session),
) -> schemas.GetTimeSpanModel:
    """
    Gets the range for which each asset in the scenario has data.
    """
    try:
        result = forecast_controller.get_asset_timespan(
            db, scenario, asset_name=asset_name, feeders=feeders
        )
    except exceptions.AssetNotFoundException as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Asset `{asset_name}` not found.") from e
    except exceptions.ScenarioNotFoundException as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Scenario `{scenario}` not found.") from e

    return result


@router.get(
    "/{scenario}/asset_events/timespan",
    response_model=schemas.GetTimeSpanModel,
    description=load_resource("timespan_response"),
    tags=["spec-required"],
)
async def get_event_timespans(
    scenario: schemas.ScenarioID = Path(
        ...,
        description=(
            "The id of the scenario to get data for. This must be an **exact** "
            "match to an ID returned from the /scenarios API."
        ),
    ),
    feeders: Optional[List[str]] = Query(
        None, description="The feeders for which the asset data should be retrieved."
    ),
    asset_name: Optional[str] = Query(
        None, description="The name of the asset for which the asset data should be retrieved."
    ),
    _: bool = Depends(validate_token),
    db: Session = Depends(get_db_session),
) -> schemas.GetTimeSpanModel:
    """
    Gets the range for which each asset event in the scenario has data.
    """
    try:
        result = forecast_controller.get_event_timespan(
            db, scenario, asset_name=asset_name, feeders=feeders
        )
    except exceptions.AssetNotFoundException as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Asset `{asset_name}` not found.") from e
    except exceptions.ScenarioNotFoundException as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Scenario `{scenario}` not found.") from e

    return result


@router.post(
    "/{scenario}/asset_schedules/{feeder}",
    tags=["test-only"],
    status_code=status.HTTP_201_CREATED,
)
async def add_schedules(
    scenario: schemas.ScenarioID,
    feeder: schemas.FeederID,
    new_schedules: schemas.AddNewSchedulesModel,
    _: bool = Depends(validate_token),
    db: Session = Depends(get_db_session),
):
    """
    Add schedule data to a scenario.

    ## Use Case
    This exists for testing purposes only. It is not part of the external schedule implementation
    and does not need to be implemented as part of the specification.
    """
    try:
        forecast_controller.add_schedules(db, scenario, feeder, new_schedules)
    except IndexError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Asset schedules array has more elements than time stamps array",
        )
    except exceptions.BadAssetScheduleTimeIntervalException:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Asset schedule data should be evenly sampled at *hourly* intervals",
        )
    return Response(status_code=status.HTTP_201_CREATED)


@router.get(
    "/{scenario}/asset_schedules",
    response_model=schemas.GetSchedulesResponseModel,
    description=load_resource("schedule_response"),
    tags=["spec-required"],
)
async def get_schedules(
    scenario: schemas.ScenarioID = Path(
        ...,
        description=(
            "The id of the scenario to get data for. This must be an **exact** "
            "match to an ID returned from the /scenarios API."
        ),
    ),
    start_datetime: datetime = Query(
        ...,
        description="The start time of the range being requested (inclusive, ISO8601 UTC).",
    ),
    end_datetime: datetime = Query(
        ...,
        description="The end time of the range being requested (exclusive, ISO8601 UTC).",
    ),
    time_interval: schemas.TimeInterval = Query(
        ..., description="The interval which the returned data should be at."
    ),
    interpolation_method: schemas.InterpolationMethod = Query(
        ...,
        description="The interpolation method to be used to fill in missing datapoints",
    ),
    sampling_mode: schemas.SamplingMode = Query(
        ...,
        description="The sampling method to be used when going from smaller to larger intervals.",
    ),
    feeders: Optional[List[str]] = Query(
        None, description="The feeders for which the asset data should be retrieved."
    ),
    asset_name: Optional[str] = Query(
        None, description="The name of the asset for which the asset data should be retrieved."
    ),
    _: bool = Depends(validate_token),
    db: Session = Depends(get_db_session),
) -> schemas.GetSchedulesResponseModel:
    """
    Gets the asset schedule data for a single asset or all assets.
    """

    # this is actually implemented and works fine as of writing this but we are
    # intentionnally preventing this from working for testing purposes
    if time_interval == schemas.TimeInterval.YEAR_1:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No yearly aggregation available")
    if time_interval == schemas.TimeInterval.MIN_5:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No 5 minute interpolation available")
    if asset_name is None and feeders is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "One of feeders or asset_name must be specified",
        )
    try:
        result = forecast_controller.get_asset_data(
            db,
            scenario,
            start_datetime,
            end_datetime,
            time_interval,
            interpolation_method,
            sampling_mode,
            asset_name=asset_name,
            feeders=feeders,
        )
    except exceptions.ScenarioNotFoundException as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Scenario `{scenario}` not found") from e
    except exceptions.AssetNotFoundException as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Asset `{asset_name}` not found.") from e
    return result


@router.post(
    "/{scenario}/asset_events/{feeder}",
    tags=["test-only"],
    status_code=status.HTTP_201_CREATED,
)
async def add_events(
    scenario: schemas.ScenarioID,
    feeder: schemas.FeederID,
    new_events: schemas.AddNewEventsModel,
    _: bool = Depends(validate_token),
    db: Session = Depends(get_db_session),
):
    """
    Add asset events to feeder.

    ## Use Case
    This exists for testing purposes only. It is not part of the external schedule implementation
    and does not need to be implemented as part of the specification.
    """

    forecast_controller.add_events(db, scenario, feeder, new_events)
    return Response(status_code=status.HTTP_201_CREATED)


@router.get(
    "/{scenario}/asset_events",
    response_model=schemas.GetEventsResponseModel,
    description=load_resource("events_response"),
    tags=["spec-required"],
)
async def get_events(
    scenario: schemas.ScenarioID = Path(
        ...,
        description=(
            "The id of the scenario to get data for. This must be an **exact** "
            "match to an ID returned from the /scenarios API."
        ),
    ),
    start_datetime: datetime = Query(
        ...,
        description="The start time of the range being requested (inclusive, ISO8601 UTC).",
    ),
    end_datetime: datetime = Query(
        ...,
        description="The end time of the range being requested (exclusive, ISO8601 UTC).",
    ),
    feeders: Optional[List[str]] = Query(
        None, description="The feeders for which the asset data should be retrieved."
    ),
    asset_name: Optional[str] = Query(
        None, description="The name of the asset for which the asset data should be retrieved."
    ),
    event_type: Optional[List[schemas.AssetEventType]] = Query(
        None,
        description="The type of the event for which the asset data should be retrieved.",
    ),
    _: bool = Depends(validate_token),
    db: Session = Depends(get_db_session),
) -> schemas.GetEventsResponseModel:
    """
    Gets the asset event data for a single asset or all assets.
    """
    if asset_name is None and feeders is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "One of feeders or asset_name must be specified",
        )

    try:
        result = forecast_controller.get_asset_events_data(
            db,
            scenario,
            start_datetime,
            end_datetime,
            event_type=event_type,
            asset_name=asset_name,
            feeders=feeders,
        )
    except exceptions.ScenarioNotFoundException as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Scenario `{scenario}` not found") from e
    except exceptions.AssetNotFoundException as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Asset {asset_name} not found.") from e
    return result
