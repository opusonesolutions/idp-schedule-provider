from typing import List, Sequence, Tuple, cast

from idp_schedule_provider.forecaster import schemas


def resample_data(
    time_interval: schemas.TimeInterval,
    interpolation_method: schemas.InterpolationMethod,
    sampling_mode: schemas.SamplingMode,
    response_data: schemas.GetSchedulesResponseModel,
) -> schemas.GetSchedulesResponseModel:
    """
    Basic data resampling

    ## Warning
    This implementation makes many assumptions which are probably not true about real data
    and is therefore *not* production ready. Do not rely on this being correct for your
    implementation.

    - stored data is evenly sampled at *hourly* intervals
    - there is no missing data
    - no discrete variables are supported (eg. OPEN/CLOSED state of switches)

    additionally no effort has been made to optimize for performance
    """
    # if there are no timestamp, don't try to resample
    if len(response_data.timestamps) == 0:
        return response_data

    if time_interval > schemas.TimeInterval.HOUR_1:
        delta = time_interval.get_delta()
        # get the ranges of datapoints which would be merged
        ranges: List[Tuple[int, int]] = []
        start_idx = 0
        for index in range(len(response_data.timestamps)):
            if response_data.timestamps[index] >= response_data.timestamps[start_idx] + delta:
                ranges.append((start_idx, index))
                start_idx = index
        ranges.append((start_idx, len(response_data.timestamps)))
        # iterate through in reverse order to avoid index changes
        for start_idx, stop_idx in reversed(ranges):
            if sampling_mode == schemas.SamplingMode.WEIGHTED_AVERAGE:
                for entries in response_data.assets.values():
                    entries[start_idx] = _weighted_average(entries[start_idx:stop_idx])

            del response_data.timestamps[start_idx + 1 : stop_idx]
            for entries in response_data.assets.values():
                del entries[start_idx + 1 : stop_idx]
    elif time_interval < schemas.TimeInterval.HOUR_1:
        delta = time_interval.get_delta()

        num_to_insert = round(60 / delta.minutes) - 1

        # upsample
        num_timepoints = len(response_data.timestamps)
        for index in range(num_timepoints):
            pos_to_update = num_timepoints - index
            for i in reversed(range(num_to_insert)):
                response_data.timestamps.insert(
                    pos_to_update, response_data.timestamps[pos_to_update - 1] + (i + 1) * delta
                )
                for entries in response_data.assets.values():
                    if interpolation_method == schemas.InterpolationMethod.LOCF:
                        entries.insert(pos_to_update, entries[pos_to_update - 1])
                    elif interpolation_method == schemas.InterpolationMethod.NOCB:
                        entries.insert(pos_to_update, entries[pos_to_update])
                    else:
                        # add empty values
                        entries.insert(pos_to_update, {})

            for entries in response_data.assets.values():
                _linear_interpolate(entries)

    return response_data


def _weighted_average(entries_to_average: Sequence[schemas.ScheduleEntry]) -> schemas.ScheduleEntry:
    new_entry: schemas.ScheduleEntry = {}
    for variable in entries_to_average[0].keys():
        values = [val[variable] for val in entries_to_average]
        if isinstance(values[0], float):
            balanced_values = cast(Sequence[float], values)
            sum_of_values = sum(val for val in balanced_values)
            new_entry[variable] = sum_of_values / len(entries_to_average)
        elif isinstance(values[0], schemas.UnbalancedScheduleValue):
            unbalanced_values = cast(Sequence[schemas.UnbalancedScheduleValue], values)
            new_value = schemas.UnbalancedScheduleValue()
            # or 0 is only safe if the no missing data assumption is true
            new_value.A = sum(val.A or 0 for val in unbalanced_values) / len(entries_to_average)
            new_value.B = sum(val.B or 0 for val in unbalanced_values) / len(entries_to_average)
            new_value.C = sum(val.C or 0 for val in unbalanced_values) / len(entries_to_average)
            new_entry[variable] = new_value

    return new_entry


def _linear_interpolate(entries: List[schemas.ScheduleEntry]):
    for idx, entry in enumerate(entries):
        if entry:
            continue  # already have a value
        try:
            _previous = entries[idx - 1]
        except IndexError:
            continue  # cannot interpolate if no previous datapoint

        try:
            next_idx = idx
            while not entries[next_idx]:
                next_idx += 1
            _next = entries[next_idx]
        except IndexError:
            continue  # cannot interpolate if no next datapoint

        def lerp(_prev: float, _next: float) -> float:
            return _prev + ((_next - _prev) / (next_idx - idx + 1))

        new_entry: schemas.ScheduleEntry = {}
        for variable in _previous.keys():
            prev_value = _previous[variable]
            next_value = _next[variable]

            if isinstance(prev_value, schemas.UnbalancedScheduleValue) and isinstance(
                next_value, schemas.UnbalancedScheduleValue
            ):
                new_value = schemas.UnbalancedScheduleValue()
                if prev_value.A is not None and next_value.A is not None:
                    new_value.A = lerp(prev_value.A, next_value.A)
                if prev_value.B is not None and next_value.B is not None:
                    new_value.B = lerp(prev_value.B, next_value.B)
                if prev_value.C is not None and next_value.C is not None:
                    new_value.C = lerp(prev_value.C, next_value.C)

                new_entry[variable] = new_value

            elif isinstance(next_value, float) and isinstance(prev_value, float):
                new_entry[variable] = lerp(prev_value, next_value)
            else:
                new_entry[variable] = None

        entries[idx] = new_entry
