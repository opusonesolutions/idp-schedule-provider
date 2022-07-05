import pytest

from idp_schedule_provider.forecaster import exceptions
from idp_schedule_provider.forecaster.controller import validate_schedules
from idp_schedule_provider.forecaster.schemas import AddNewSchedulesModel


@pytest.mark.parametrize(
    "schedules, expected_result",
    [
        (
            {
                "time_stamps": [
                    "2000-01-01T01:00:00+00:00",
                    "2000-01-01T02:00:00+00:00",
                ],
                "assets": {
                    "feeder1": [
                        {},
                        {},
                    ],
                },
            },
            True,
        ),
        (
            {
                "time_stamps": [
                    "2000-01-01T23:00:00+00:00",
                    "2000-01-02T00:00:00+00:00",
                ],
                "assets": {
                    "feeder1": [
                        {},
                        {},
                    ],
                },
            },
            True,
        ),
        (
            {
                "time_stamps": [
                    "2000-01-01T01:00:00+00:00",
                    "2000-01-01T00:00:00+00:00",
                ],
                "assets": {
                    "feeder1": [
                        {},
                        {},
                    ],
                },
            },
            exceptions.BadAssetScheduleTimeIntervalException,
        ),
        (
            {
                "time_stamps": [
                    "2000-01-03T00:00:00+00:00",
                    "2000-01-02T00:00:00+00:00",
                ],
                "assets": {
                    "feeder1": [
                        {},
                        {},
                    ],
                },
            },
            exceptions.BadAssetScheduleTimeIntervalException,
        ),
        (
            {
                "time_stamps": [
                    "2000-01-01T01:00:00+00:00",
                    "2000-01-03T00:00:00+00:00",
                ],
                "assets": {
                    "feeder1": [{}],
                },
            },
            IndexError,
        ),
    ],
)
def test_validate_schedules(schedules, expected_result):
    schedules = AddNewSchedulesModel.parse_obj(schedules)
    if expected_result is exceptions.BadAssetScheduleTimeIntervalException:
        with pytest.raises(exceptions.BadAssetScheduleTimeIntervalException):
            validate_schedules(schedules)
    elif expected_result is IndexError:
        with pytest.raises(IndexError):
            validate_schedules(schedules)
    else:
        validate_schedules(schedules)
