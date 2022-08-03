Gets the asset event data for a single asset or all assets.

## Use Case

This single asset version of this API will be used for the following

- Displaying graphs in the user interface

The many asset version of this API will be used for the following

- Loading event data for analysis

## General Requirements and Guidelines

<details>

### Performance Guidelines

This endpoint provides the asset schedule data for both simulation and UI which
will query very different amounts of data and have different performance expectations.

#### Single Asset Requests (Primarily User Interface Requests)

These requests are for data for single asset over any time range.
They populate graphs and charts in the user interface. If they are slow,
the user interface will be slow so our expectation is the target response time
should be under 1 second.

#### Multiple Asset Requests (Primarily Analysis Requests)

These requests are for data for all of the assets in the network but have a smaller
maximum time range. They are used to populate the data for assets when starting
an analysis. Because these are used in the background and request a much larger
amounts of data, their performance is expected to be slower. Ideally all responses
of this type are <30s however longer responses will be accepted, they will just
impact total analysis time.

With current product functionality, we never request time ranges greater than 1
month for multiple asset reqests.

</details>

## Event Variables

### Electric Vehicle Charging Station (EV) Events

<details>
EV events will be used when an EV is in *Global* control mode and the specified analysis objective is an OPF.
When in this mode the optimization engine will make use of the provided events to determine how to
optimally charge the electric vehicle to meet the desired objective.

If no charging events are provided or there are no events active for a timepoint,
the EV station is assumed to be doing nothing and will consume no power.

| Variable Name          | Description                                                              | Units |
| ---------------------- | ------------------------------------------------------------------------ | ----- |
| start_datetime         | UTC timestamp indicating when the EV is able to start charging (ISO8601) | n/a   |
| end_datetime           | UTC timestamp indicating when the EV has stopped charging (IS08601)      | n/a   |
| event_type             | This should always be "electric_vehicle_charge" for this event           | n/a   |
| pf                     | power factor of the charging event (number between 0 and 1)              | n/a   |
| p_max                  | maximum real power of the charging event                                 | W     |
| start_soc              | starting state-of-charge of the EV battery (note: 0 = 0% and 1 = 100%)   | %     |
| total_battery_capacity | total capacity of the EV battery                                         | Wh    |

</details>

### Control Mode Events

<details>
Control mode events will be used for an asset to determine the control mode it should be in for
analysis purposes when performing analyses.

If no control mode events are provided or there are no events active for a timepoint, the asset is assumed to be controlled using the mode specified in the network model.

| Variable Name  | Description                                                              | Units |
| -------------- | ------------------------------------------------------------------------ | ----- |
| start_datetime | UTC timestamp indicating when the control mode event begins (ISO8601)    | n/a   |
| end_datetime   | UTC timestamp indicating when the control mode event ends (IS08601)      | n/a   |
| event_type     | This should always be "control_mode" for this event                      | n/a   |
| control_mode   | The mode this asset should be in for the duration of start/end timestamp | n/a   |

</details>
