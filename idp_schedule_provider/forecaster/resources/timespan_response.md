Gets the range for which each asset in the scenario has data.

## Use Case
This operation will be used for the following:
* Determining if an asset has schedule data
* Identifying which assets are included in the feeder schedule
* Determining the timerange in which an analysis can be run.

## General Requirements and Guidelines

<details>

### Performance Guidelines
This endpoint provides the timespan data primarily for user interface interactions.
If they are slow, the user interface will be slow so our expectation is the
target response time should be under 1 second for these requests.

### Electric Vehicle Charging Events
Electric vehicle charging events are a special case for this endpoint. For EV
charging events, the start_datetime should be the earliest charge_event_start of
all charging events and the end_datetime should be the last charge_event_end of
all charging events for the specified asset.

</details>
