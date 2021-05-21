from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm.session import Session

from idp_schedule_provider.authentication.auth import validate_token
from idp_schedule_provider.forecaster import controller as forecast_controller
from idp_schedule_provider.forecaster import exceptions, schemas
from idp_schedule_provider.forecaster.database import get_db_session

router = APIRouter()


@router.post("/seed_data")
async def seed_db(db: Session = Depends(get_db_session)):
    forecast_controller.seed(db)


@router.get("/scenario", response_model=schemas.GetScenariosResponseModel)
async def get_scenarios(_=Depends(validate_token), db: Session = Depends(get_db_session)):
    """
    Gets all scenarios currently available from the schedule provider.

    ## Use Case
    This operation will be used to allow the user to choose between multiple scenarios available.
    If there is only a single scenario available.
    """
    return forecast_controller.get_all_scenarios(db)


@router.get("/{scenario}/asset_schedules/timespan", response_model=schemas.GetTimeSpanModel)
async def get_schedule_timespans(
    scenario: schemas.ScenarioID = Path(..., description="The id of the scenario to get data for"),
    feeders: Optional[List[str]] = Query(
        None, description="The feeders for which the asset data should be retrieved."
    ),
    asset_name: Optional[str] = Query(
        None, description="The name of the asset for which the asset data should be retrieved."
    ),
    _=Depends(validate_token),
    db: Session = Depends(get_db_session),
):
    """
    Gets the range for which each asset in the scenario has data.

    ## Use Case
    This operation will be used for the following:
    * Determining if an asset has schedule data
    * Identifying which assets are included in the feeder schedule
    * Determining the timerange in which an analysis can be run.
    """
    try:
        if asset_name is not None:
            result = forecast_controller.get_asset_timespan(db, scenario, asset_name)
        else:
            result = forecast_controller.get_scenario_timespan(db, scenario, feeders)
    except exceptions.AssetNotFoundException:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    except exceptions.ScenarioNotFoundException:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scenario not found")

    return result


@router.get("/{scenario}/asset_schedules", response_model=schemas.GetSchedulesResponseModel)
async def get_schedules(
    scenario: schemas.ScenarioID = Path(..., description="The id of the scenario to get data for"),
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
    _=Depends(validate_token),
    db: Session = Depends(get_db_session),
):
    """
    Gets the asset schedule data for a single asset or all assets.

    ## Use Case
    This single asset version of this API will be used for the following
    * Displaying graphs in the user interface

    The many asset version of this API will be used for the following
    * Loading schedule data for analysis
    """

    # this is actually implemented and works fine as of writing this but we are
    # intentionnally preventing this from working for testing purposes
    if time_interval == schemas.TimeInterval.YEAR_1:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No yearly aggregation available")

    try:
        if asset_name is not None:
            result = forecast_controller.get_asset_data(
                db,
                scenario,
                start_datetime,
                end_datetime,
                time_interval,
                interpolation_method,
                sampling_mode,
                asset_name,
            )
        elif feeders is not None:
            result = forecast_controller.get_scenario_data(
                db,
                scenario,
                start_datetime,
                end_datetime,
                time_interval,
                interpolation_method,
                sampling_mode,
                feeders,
            )
        else:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "One of feeders or asset_name must be specified",
            )
    except exceptions.ScenarioNotFoundException:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scenario not found")
    except exceptions.AssetNotFoundException:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")

    return result
