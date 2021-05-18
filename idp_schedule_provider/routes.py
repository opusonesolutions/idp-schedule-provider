from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from idp_schedule_provider import exceptions, forecaster, models

router = APIRouter()


@router.get("/scenario", response_model=models.GetScenariosModel)
async def get_scenarios():
    return forecaster.get_all_scenarios()


@router.get("/{scenario}/asset_schedules/timespan", response_model=models.GetTimeSpanModel)
async def get_schedule_timespans(scenario: models.ScenarioID):
    try:
        result = forecaster.get_scenario_timespan(scenario)
    except exceptions.ScenarioNotFoundException:
        raise HTTPException(404, "Scenario not found")

    return result


@router.get("/{scenario}/asset_schedules", response_model=models.GetSchedulesResponseModel)
async def get_schedules(
    # path params
    scenario: models.ScenarioID,
    # query params
    start_time: datetime,
    end_time: datetime,
    time_interval: models.TimeInterval,
    interpolation_method: models.InterpolationMethod,
    sampling_mode: models.SamplingMode,
    feeders: Optional[List[str]] = None,
    asset_name: Optional[str] = None,
):
    try:
        if asset_name is not None:
            result = forecaster.get_asset_data(
                scenario,
                start_time,
                end_time,
                time_interval,
                interpolation_method,
                sampling_mode,
                asset_name,
            )
        elif feeders is not None:
            result = forecaster.get_scenario_data(
                scenario,
                start_time,
                end_time,
                time_interval,
                interpolation_method,
                sampling_mode,
                feeders,
            )
        else:
            raise HTTPException(400, "One of feeders or asset_name must be specified")
    except exceptions.ScenarioNotFoundException:
        raise HTTPException(404, "Scenario not found")

    return result
