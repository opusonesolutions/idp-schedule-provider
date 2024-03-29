Gets the asset schedule data for a single asset or all assets.

## Use Case

This single asset version of this API will be used for the following

- Displaying graphs in the user interface

The many asset version of this API will be used for the following

- Loading schedule data for analysis

## General Requirements and Guidelines

<details>

### Timestamp and Asset Value array consistency

The array of timestamps must be exactly the same length as the array of values for
each asset. The timestamps will be assumed to map 1:1 with the array of datapoints.
If a datapoint is intentionally being skipped, use an empty object.

### Missing Data

The data returned by the API should not be missing any timepoints or data for assets.
In the absence of data, assets will fallback on their default behaviors. See the
Schedule Variables section for more information on defaults.

### Data Alignment

Timestamps must be aligned to the interval size.

For example:
for a 5 minute interval, your datetimes must be a multiple of 5 minutes
past the hour. some examples of valid 5 minute datetimes:
2000-01-01T23:00:00Z, 2000-01-01T23:05:00Z, 2000-01-01T23:35:00Z
for a 30 minute interval, your datetimes must be a multiple of 30 minutes
past the hour. some example of valid 30 minute datetimes:
2000-01-01T00:00:00Z, 2000-01-01T01:00:00Z, 2000-01-01T01:30:00Z

### Performance Guidelines

This endpoint provides the asset schedule data for both simulation and UI which
will query very different amounts of data and have different performance expectations.

#### Single Asset Requests (Primarily User Interface Requests)

These requests are for data for single asset over any time range.
They populate graphs and charts in the user interface. If they are slow,
the user interface will be slow so our expectation is the target response time
should be under 1 second.

We perform these queries with certain breakpoints where we will shift the
aggregation level to ensure the number of datapoints we retrieve remains
relatively small. None of the requests performed should result in a response
with greater than 200 datapoints.

**Sample Queries**

| start_datetime       | end_datetime         | time_interval | response length |
| -------------------- | -------------------- | ------------- | --------------- |
| 2000-01-01T00:00:00Z | 2000-12-31T23:59:59Z | 1 month       | 12 timepoints   |
| 2000-01-01T00:00:00Z | 2000-01-31T23:59:59Z | 1 day         | 31 timepoints   |
| 2000-01-01T00:00:00Z | 2000-01-01T23:59:59Z | 1 hour        | 24 timepoints   |
| 2000-01-01T00:00:00Z | 2000-01-01T01:59:59Z | 5 minutes     | 24 timepoints   |

#### Multiple Asset Requests (Primarily Analysis Requests)

These requests are for data for all of the assets in the network but have a smaller
maximum time range. They are used to populate the data for assets when starting
an analysis. Because these are used in the background and request a much larger
amounts of data, their performance is expected to be slower. Ideally all responses
of this type are <30s however longer responses will be accepted, they will just
impact total analysis time.

With current product functionality, we never request time ranges greater than 1
month for multiple asset reqests.

**Sample Queries**

| start_datetime       | end_datetime         | time_interval | response length         |
| -------------------- | -------------------- | ------------- | ----------------------- |
| 2000-01-01T00:00:00Z | 2000-01-31T23:59:59Z | 1 day         | 31 timepoints per asset |
| 2000-01-01T00:00:00Z | 2000-01-01T23:59:59Z | 1 hour        | 24 timepoints per asset |
| 2000-01-01T00:00:00Z | 2000-01-01T01:59:59Z | 5 minutes     | 24 timepoints per asset |

</details>

## Schedule Variables

### Feeder / Substation Schedules

<details>
Feeders and substations support a balanced load/gen schedules.

#### Load/Gen Schedule

A Load/Gen schedule can be provided for a feeder/substation.
The load and generation values will be allocated throughout the equipment container
it is associated with. More details on load allocation are available through the
GridOS product documentation.

We require all timepoints to be present for feeders/substations if data is being
provided. Gaps are likely to cause the analysis to fail or behave unpredictably.

| Variable Name | Description                                     | Units |
| ------------- | ----------------------------------------------- | ----- |
| load          | total loading of all assets in the feeder       | W     |
| load_pf       | power factor of the feeder load                 | p.u   |
| generation    | total generation of all assets in of the feeder | W     |
| generation_pf | power factor of the feeder generation           | p.u   |

#### Cost of Violations Schedule

A Cost of Violations schedule can be provided for a feeder/substation.
The costs will be applied to all assets in that feeder/substation. These will take
precedence over any values in the network model however values specified on that
asset itself will take precedence over these.

The values can either be a single value or a curve that changes the cost (`y`) based on how much
the rating is violated by.

A simple curve example of [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 100}] means that

- Having any value below 100% of the equipment rating will have no cost
- Any value greater than 100% of the equipment rating will have a cost of $1 per 1%

| Variable Name          | Description                              | Units   |
| ---------------------- | ---------------------------------------- | ------- |
| current_violation_cost | The cost of violating the current rating | $/ratio |
| voltage_violation_cost | The cost of violating the voltage rating | $/ratio |
| power_violation_cost   | The cost of violating the power rating   | $/ratio |

##### Example(s)

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "feeder_1": [
            {
                "load": 450000,
                "load_pf": 0.9,
                "generation": 45000,
                "generation_pf": 0.95,
                "current_violation_cost": 2
            },
            {
                "load": 550000,
                "load_pf": 0.86,
                "generation": 75000,
                "generation_pf": 0.95,
                "current_violation_cost": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 100}]
            },
            ...
        ],
    }
}
```

</details>

### Load / Energy Consumer Schedules

<details>
Loads/Energy Consumers support both balanced and unbalanced P,Q schedules, as well as cost schedules.

#### PQ Schedule

If a PQ schedule is provided for a load it will always be used.
The load will follow the specified PQ values and no optimization will be performed unless
the load is otherwise configured with demand response characteristics.

For any timepoints where the PQ values are not specified, P,Q are assumed to be 0.

| Variable Name | Description                | Units |
| ------------- | -------------------------- | ----- |
| p             | real power consumption     | W     |
| q             | reactive power consumption | VAR   |

### Cost Schedule

If a cost schedule is provided for a load it will be used when performing
Cost Optimization analyses.

The values can either be a single value that is used throughout that timepoint,
or a curve that changes the cost (`y`) based on usage.

| Variable Name                          | Description                            | Units          |
| -------------------------------------- | -------------------------------------- | -------------- |
| active_energy_cost (as a single value) | Cost of procuring energy from device   | $/Wh           |
| active_energy_cost (as a curve)        | Curve for the cost of procuring energy | x = W, y = $/h |

<details>
<summary>Balanced Asset Example</summary>

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "load_1": [
            {
                "p": 450000,
                "q": 500,
                "active_energy_cost": [{"x": 100, "y": 150}, {"x": 200, "y": 250}]
            },
            {
                "p": 550000,
                "q": 1000,
                "active_energy_cost": 50
            },
            ...
        ],
    }
}
```

</details>
<details>
<summary>Unbalanced Asset Example</summary>

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "load_1": [
            {
                "p": { "A": 100000, "B": 225000, "C": 125000},
                "q": { "A": 5000, "B": 7000, "C": 6000},
                "active_energy_cost": [{"x": 100, "y": 150}, {"x": 200, "y": 250}]
            },
            {
                "p": { "A": 100000, "B": 325000, "C": 125000},
                "q": { "A": 5000, "B": 8000, "C": 6000},
                "active_energy_cost": 50
            },
            ...
        ],
    }
}
```

</details>

</details>

### Electric Vehicle Station (EV) Schedules

<details>

#### PQ Schedule

A PQ schedule will be used for an EV if it is in scheduled mode.
The EV will follow the specified PQ values and no optimization will be performed.

For any timepoints where the PQ values are not specified, P,Q are assumed to be 0.

| Variable Name | Description                | Units |
| ------------- | -------------------------- | ----- |
| p             | real power consumption     | W     |
| q             | reactive power consumption | VAR   |

</details>

### Photovoltaic (PV) Schedules

<details>
Photovoltaics only support a PQ schedule and a cost schedule

#### PQ Schedule

A PQ schedule will be used for an PV if it is in scheduled mode.
The PV will follow the specified PQ values and no optimization will be performed.

For any timepoints where the PQ values are not specified, P,Q are will be allocated
proportionally from the substation generation.

| Variable Name | Description                | Units |
| ------------- | -------------------------- | ----- |
| p             | real power consumption     | W     |
| q             | reactive power consumption | VAR   |

### Cost Schedule

The values can either be a single value that is used throughout that timepoint,
or a curve that changes the cost (`y`) based on usage.

| Variable Name      | Description                    | Units |
| ------------------ | ------------------------------ | ----- |
| active_energy_cost | the cost of energy consumption | $/Wh  |

| Variable Name                          | Description                            | Units          |
| -------------------------------------- | -------------------------------------- | -------------- |
| active_energy_cost (as a single value) | Cost of procuring energy from device   | $/Wh           |
| active_energy_cost (as a curve)        | Curve for the cost of procuring energy | x = W, y = $/h |

</details>

### Battery (BESS) Schedules

<details>

BESS support PQ, SoC and Cost Schedules

#### PQ Schedule

A PQ schedule will be used for a BESS if it is in scheduled mode.
The BESS will follow the specified PQ values and no optimization will be performed.

For any timepoints where the PQ values are not specified, P,Q are assumed to be 0.

| Variable Name | Description                                                  | Units |
| ------------- | ------------------------------------------------------------ | ----- |
| p             | real power (positive = charging, negative = discharging)     | W     |
| q             | reactive power (positive = charging, negative = discharging) | VAR   |

#### Soc Schedule

A SoC schedule will be used for a BESS if it is in global mode. The optimization will control
the PQ of the battery to optimally dispatch and the SoC schedule will be used to cap the
min and max charge levels.

For any timepoints where the SoC values are not specified, the min and max SoC
of the battery asset will be used.

| Variable Name | Description                                       | Units |
| ------------- | ------------------------------------------------- | ----- |
| min_SOC       | value between 0 and 1 (where 0 = 0% and 1 = 100%) | %     |
| max_SOC       | value between 0 and 1 (where 0 = 0% and 1 = 100%) | %     |

### Cost Schedule

If a cost schedule is provided for a load it will be used when performing
Cost Optimization analyses.

The values can either be a single value that is used throughout that timepoint,
or a curve that changes the cost (`y`) based on usage.

| Variable Name                          | Description                            | Units          |
| -------------------------------------- | -------------------------------------- | -------------- |
| active_energy_cost (as a single value) | Cost of procuring energy from device   | $/Wh           |
| active_energy_cost (as a curve)        | Curve for the cost of procuring energy | x = W, y = $/h |

</details>

### Capacitor/Reactor Schedules

<details>

Capacitors support being connected and disconnected via schedules. This can either be provided
per-phase or as a single balanced value. They also support cost schedules for the cost of
operating this capacitor.

For any timepoints where the state values are not specified, the capacitor will
be assumed to be in its default connection state.

#### State Schedule

| Variable Name | Description                                                  | Units |
| ------------- | ------------------------------------------------------------ | ----- |
| state         | either 0 (indicates disconnected) or 1 (indicates connected) | n/a   |

### Cost Schedules

The values must be a single value that is used throughout that timepoint.

| Variable Name            | Description                                                 | Units       |
| ------------------------ | ----------------------------------------------------------- | ----------- |
| capacitor_operation_cost | the cost of changing the connection status of the capacitor | $/operation |

<details>
<summary>Balanced Asset Example</summary>

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "cap_1": [
            {
                "state": 1,
                "capacitor_operation_cost": 50,
            },
            {
                "state": 0,
                "capacitor_operation_cost": 50,
            }
            ...
        ],
    }
}
```

</details>
<details>
<summary>Unbalanced Asset Example</summary>

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "cap_1": [
            {
                "state": { "A": 1, "B": 0, "C": 1},
                "capacitor_operation_cost": 50
            },
            {
                "state": { "A": 1, "B": 1, "C": 1},
                "capacitor_operation_cost": 50
            },
            ...
        ],
    }
}
```

</details>

</details>

### Synchronous Machine / Combined-Heat & Power (CHP) / River Hydro Schedules

<details>

Synchronous machines and their variations support a balanced PQ schedule, as well as a cost schedule

For any timepoints where the PQ values are not specified, P,Q are assumed to be 0.

#### PQ Schedule

| Variable Name | Description               | Units |
| ------------- | ------------------------- | ----- |
| p             | real power generation     | W     |
| q             | reactive power generation | VAR   |

### Cost Schedule

The values can either be a single value that is used throughout that timepoint,
or a curve that changes the cost (`y`) based on usage.

| Variable Name                          | Description                            | Units          |
| -------------------------------------- | -------------------------------------- | -------------- |
| active_energy_cost (as a single value) | Cost of procuring energy from device   | $/Wh           |
| active_energy_cost (as a curve)        | Curve for the cost of procuring energy | x = W, y = $/h |

</details>

### Asynchronous Machine / Wind Schedules

<details>

Asynchronous machines and their variations support a balanced PQ schedule and a cost schedule.

For any timepoints where the PQ values are not specified, P,Q are will be allocated
proportionally from the substation generation.

#### PQ Schedule

| Variable Name | Description               | Units |
| ------------- | ------------------------- | ----- |
| p             | real power generation     | W     |
| q             | reactive power generation | VAR   |

### Cost Schedule

The values can either be a single value that is used throughout that timepoint,
or a curve that changes the cost (`y`) based on usage.

| Variable Name                          | Description                            | Units          |
| -------------------------------------- | -------------------------------------- | -------------- |
| active_energy_cost (as a single value) | Cost of procuring energy from device   | $/Wh           |
| active_energy_cost (as a curve)        | Curve for the cost of procuring energy | x = W, y = $/h |

</details>

### Switch Schedules

<details>

Switches support being open/closed via schedules. They can either be provided
per-phase or as a single balanced value. Switches also support violation cost schedules
which can only be specified as a balanced value.

For any timepoints where the status values are not specified, the switch will be
assumed to be in its default open/closed state.

#### Status Schedule

| Variable Name | Description                                       | Units |
| ------------- | ------------------------------------------------- | ----- |
| status        | either 0 (indicates open) or 1 (indicates closed) | n/a   |

#### Cost of Violations Schedule

A Cost of Violations schedule can be provided for a switch. These will take
precedence over any other switch violation costs.

The values can either be a single value or a curve that changes the cost (`y`) based on how much
the rating is violated by.

A simple curve example of [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 100}] means that

- Having any value below 100% of the equipment rating will have no cost
- Any value greater than 100% of the equipment rating will have a cost of $1 per 1%

| Variable Name          | Description                              | Units   |
| ---------------------- | ---------------------------------------- | ------- |
| current_violation_cost | The cost of violating the current rating | $/ratio |
| power_violation_cost   | The cost of violating the power rating   | $/ratio |

<details>
<summary>Balanced Asset Example</summary>

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "switch_1": [
            {
                "status": 1,
                "current_violation_cost": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 100}]
            },
            {
                "status": 0,
                "current_violation_cost": 2
            },
            ...
        ],
    }
}
```

</details>
<details>
<summary>Unbalanced Asset Example</summary>

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "switch_1": [
            {
                "status": { "A": 1, "B": 0, "C": 1},
                "current_violation_cost": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 100}]
            },
            {
                "status": { "A": 1, "B": 1, "C": 1},
                "current_violation_cost": 2
            },
            ...
        ],
    }
}
```

</details>

</details>

### Energy Source / Slack Schedules

<details>

Energy Sources support a balanced operating voltage schedule.

For any timepoints where the operationg voltage values are not specified, the
energy source will be assumed to use its default operating voltage.

#### Operating Voltage Schedule

| Variable Name     | Description                                    | Units |
| ----------------- | ---------------------------------------------- | ----- |
| operating_voltage | operating voltage (per unit value; >0.4, <1.6) | p.u   |

</details>

### Equivalent Substation Schedules

<details>

Equivalent substations support a balanced or unbalanced PQ schedule, as well as a cost schedule.

For any timepoints where the PQ values are not specified, P,Q are assumed to be 0.

#### PQ Schedule

| Variable Name | Description                                                 | Units |
| ------------- | ----------------------------------------------------------- | ----- |
| p             | real power (positive=consumption, negative=backfeeding      | W     |
| q             | reactive power (positive=consumption, negative=backfeeding) | VAR   |

### Cost Schedule

The values can either be a single value that is used throughout that timepoint,
or a curve that changes the cost (`y`) based on usage.

| Variable Name                          | Description                            | Units          |
| -------------------------------------- | -------------------------------------- | -------------- |
| active_energy_cost (as a single value) | Cost of procuring energy from device   | $/Wh           |
| active_energy_cost (as a curve)        | Curve for the cost of procuring energy | x = W, y = $/h |

<details>
<summary>Balanced Asset Example</summary>

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "load_1": [
            {
                "p": 450000,
                "q": 500,
                "active_energy_cost": [{"x": 100, "y": 150}, {"x": 200, "y": 250}]
            },
            {
                "p": 550000,
                "q": 1000,
                "active_energy_cost": 50
            },
            ...
        ],
    }
}
```

</details>
<details>
<summary>Unbalanced Asset Example</summary>

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "load_1": [
            {
                "p": { "A": 100000, "B": 225000, "C": 125000},
                "q": { "A": 5000, "B": 7000, "C": 6000},
                "active_energy_cost": [{"x": 100, "y": 150}, {"x": 200, "y": 250}]
            },
            {
                "p": { "A": 100000, "B": 325000, "C": 125000},
                "q": { "A": 5000, "B": 8000, "C": 6000},
                "active_energy_cost": 50
            },
            ...
        ],
    }
}
```

</details>

</details>

### Transformer/Regulator Schedules

<details>

Transformers and regulators support a balanced or unbalanced tap position schedule. They also support violation cost schedules
which can only be specified as a balanced value.

For any timepoints where the tap position values are not specified, the transformer will be
assumed to be in its default tap position.

#### Tap Schedule

| Column Name   | Description                                | Units |
| ------------- | ------------------------------------------ | ----- |
| tap_positions | integer number indicating the tap position | n/a   |

### Cost Schedules

The values must be a single value that is used throughout that timepoint.

| Variable Name      | Description                                  | Units  |
| ------------------ | -------------------------------------------- | ------ |
| tap_operation_cost | the cost of changing the tap position by one | $/step |

#### Cost of Violations Schedule

A Cost of Violations schedule can be provided for a transformer or regulator. These will take
precedence over any other violation costs for this asset. Note: As th

The values can either be a single value or a curve that changes the cost (`y`) based on how much
the rating is violated by.

A simple curve example of [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 100}] means that

- Having any value below 100% of the equipment rating will have no cost
- Any value greater than 100% of the equipment rating will have a cost of $1 per 1%

| Variable Name          | Description                              | Units   |
| ---------------------- | ---------------------------------------- | ------- |
| current_violation_cost | The cost of violating the current rating | $/ratio |
| power_violation_cost   | The cost of violating the power rating   | $/ratio |

<details><summary>Balanced Asset Example</summary>

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "transformer_1": [
            {
                "tap_positions": 1,
                "tap_operation_cost": 50,
                "power_violation_cost": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 100}],
            },
            {
                "tap_positions": 0,
                "tap_operation_cost": 50,
                "power_violation_cost": 2,
            },
            ...
        ],
    }
}
```

</details>
<details><summary>Unbalanced Asset Example</summary>

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "transformer_1": [
            {
                "tap_positions": { "A": 10, "B": 12, "C": 8},
                "tap_operation_cost": 50,
                "power_violation_cost": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 100}],
            },
            {
                "tap_positions": { "A": 12, "B": 10, "C": 8},
                "tap_operation_cost": 50,
                "power_violation_cost": 2,
            },
            ...
        ],
    }
}
```

</details>

</details>

### Line Segment Schedules

<details>

Line segments support violation cost schedules.

#### Cost of Violations Schedule

A Cost of Violations schedule can be provided for a line segment. These will take
precedence over any other violation costs for this asset.

The values can either be a single value or a curve that changes the cost (`y`) based on how much
the rating is violated by.

A simple curve example of [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 100}] means that

- Having any value below 100% of the equipment rating will have no cost
- Any value greater than 100% of the equipment rating will have a cost of $1 per 1%

| Variable Name          | Description                              | Units   |
| ---------------------- | ---------------------------------------- | ------- |
| current_violation_cost | The cost of violating the current rating | $/ratio |
| power_violation_cost   | The cost of violating the power rating   | $/ratio |

<details><summary>Example</summary>

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "line_1": [
            {
                "power_violation_cost": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 100}],
            },
            {
                "power_violation_cost": 2
            },
            ...
        ],
    }
}
```

</details>

</details>

### Connectivity Node Schedules

<details>

Connectivity Nodes support violation cost schedules.

#### Cost of Violations Schedule

A Cost of Violations schedule can be provided for a node. These will take
precedence over any other violation costs for this asset.

The values can either be a single value or a curve that changes the cost (`y`) based on how much
the rating is violated by.

A simple curve example of [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 100}] means that

- Having any value below 100% of the equipment rating will have no cost
- Any value greater than 100% of the equipment rating will have a cost of $1 per 1%

| Variable Name          | Description                              | Units   |
| ---------------------- | ---------------------------------------- | ------- |
| voltage_violation_cost | The cost of violating the voltage rating | $/ratio |
| power_violation_cost   | The cost of violating the power rating   | $/ratio |

<details><summary>Example</summary>

```json
{
    "time_interval": ...,
    "time_stamps": ...,
    "assets": {
        "node_1": [
            {
                "voltage_violation_cost": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 100}],
            },
            {
                "voltage_violation_cost": 2
            },
            ...
        ],
    }
}
```

</details>

</details>
