Gets the asset schedule data for a single asset or all assets.

## Use Case
This single asset version of this API will be used for the following
* Displaying graphs in the user interface

The many asset version of this API will be used for the following
* Loading schedule data for analysis

## General Requirements and Guidelines

<details>

### Timestamp and Asset Value array consistency
With the exception of EV charging events, the array of timestamps must be exactly
the same length as the array of values for each asset. The timestamps will be
assumed to map 1:1 with the array of datapoints. If a datapoint is intentionally
being skipped, use an empty object.

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
This endpoint provides the asset schedule data for both simulation and UI which will query very different amounts of data and have different performance expectations.

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
| -------------------- | -------------------- | ------------- | -------------   |
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

| start_datetime       | end_datetime         | time_interval | response length |
| -------------------- | -------------------- | ------------- | -------------   |
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

| Variable Name  | Description                                         | Units |
|----------------|-----------------------------------------------------|-------|
| load           | total loading of all assets in the feeder           | W     |
| load_pf        | power factor of the feeder load                     | p.u   |
| generation     | total generation of all assets in of the feeder     | W     |
| generation_pf  | power factor of the feeder generation               | p.u   |

</details>

### Eletric Vehicle Station (EV) Schedules

<details>
EVs support two types of schedules, PQ and charging event schedules

#### PQ Schedule
A PQ schedule will be used for an EV if it is in scheduled mode. 
The EV will follow the specified PQ values and no optimization will be performed.

For any timepoints where the PQ values are not specified, P,Q are assumed to be 0.

| Variable Name | Description                                          | Units |
|---------------|------------------------------------------------------|-------|
| p             | real power consumption                               | W     |
| q             | reactive power consumption                           | VAR   |

#### Charging Event Schedule
A charging event schedule will be used for an EV when it is in *Global* mode and performing an OPF. 
When in this mode the optimization engine will make use of the provided events to determine how to
optimally charge the electric vehicle to meet the desired objective.

This schedule type is unique in that the interpolation and sampling parameters
of the API are not relevant to these values. There is no way to downsample the
schedules in a way that would have any real meaning. What this does mean is if
you are providing an extremely large number of schedules of the timeperiod,
there could be performance impacts. Additionally these values don't need to be
synchronized with the timestamps, however they *do* need to align to the
interval provided.

If no charging events are provided, the EV Station is assumed to be doing nothing
and will consume no power.

| Variable Name          | Description                                                             | Units |
|------------------------|-------------------------------------------------------------------------|-------|
| pf                     | power factor of the charging event  (number between 0 and 1)            | n/a   |
| p_max                  | maximum real power of the charging event                                | W     |
| start_soc              | starting state-of-charge of the EV battery (note: 0 = 0% and 1 = 100%)  | %     |
| total_battery_capacity | total capacity of the EV battery                                        | Wh    |

</details>

### Photovoltaic (PV) Schedules

<details>
Photovoltaics only support a PQ schedule

#### PQ Schedule
A PQ schedule will be used for an PV if it is in scheduled mode. 
The PV will follow the specified PQ values and no optimization will be performed.

For any timepoints where the PQ values are not specified, P,Q are will be allocated
proportionally from the substation generation.

| Variable Name | Description                                          | Units |
|---------------|------------------------------------------------------|-------|
| p             | real power consumption                               | W     |
| q             | reactive power consumption                           | VAR   |

</details>

### Battery (BESS) Schedules

<details>

BESS support two types of schedules, PQ and SoC schedules

#### PQ Schedule
A PQ schedule will be used for a BESS if it is in scheduled mode. 
The BESS will follow the specified PQ values and no optimization will be performed.

For any timepoints where the PQ values are not specified, P,Q are assumed to be 0.

| Variable Name | Description                                                       | Units |
|---------------|-------------------------------------------------------------------|-------|
| p             | real power (positive = charging, negative = discharging)          | W     |
| q             | reactive power (positive = charging, negative = discharging)      | VAR   |

#### Soc Schedule
A SoC schedule will be used for a BESS if it is in global mode. The optimization will control
the PQ of the battery to optimally dispatch and the SoC schedule will be used to cap the
min and max charge levels.

For any timepoints where the SoC values are not specified, the min and max SoC
of the battery asset will be used.

| Variable Name | Description                                          | Units |
|---------------|------------------------------------------------------|-------|
| min_SOC       | value between 0 and 1  (where 0 = 0% and 1 = 100%)   | %     |
| max_SOC       | value between 0 and 1  (where 0 = 0% and 1 = 100%)   | %     |

</details>

### Capacitor/Reactor Schedules

<details>

Capacitors support being connected and disconnected via schedules. This can either be provided
per-phase or as a single balanced value.

For any timepoints where the state values are not specified, the capacitor will
be assumed to be in its default connection state.

#### Balanced Schedule
| Variable Name | Description                                                       | Units |
|---------------|-------------------------------------------------------------------|-------|
| state         | either 0 (indicates disconnected) or 1  (indicates connected)     | n/a   |

#### Unbalanced Schedule
| Variable Name | Description                                                       | Units |
|---------------|-------------------------------------------------------------------|-------|
| state_a       | either 0 (indicates disconnected) or 1  (indicates connected)     | n/a   |
| state_b       | either 0 (indicates disconnected) or 1  (indicates connected)     | n/a   |
| state_c       | either 0 (indicates disconnected) or 1  (indicates connected)     | n/a   |

</details>

### Synchronous Machine / Combined-Heat & Power (CHP) / River Hydro Schedules

<details>

Synchronous machines and their variations support a balanced PQ schedule.

For any timepoints where the PQ values are not specified, P,Q are assumed to be 0.

#### Balanced Schedule
| Variable Name | Description                                          | Units |
|---------------|------------------------------------------------------|-------|
| p             | real power generation                                | W     |
| q             | reactive power generation                            | VAR   |

</details>

### Asynchronous Machine / Wind Schedules

<details>

Asynchronous machines and their variations support a balanced PQ schedule.

For any timepoints where the PQ values are not specified, P,Q are will be allocated
proportionally from the substation generation.

#### Balanced Schedule
| Variable Name | Description                                          | Units |
|---------------|------------------------------------------------------|-------|
| p             | real power generation                                | W     |
| q             | reactive power generation                            | VAR   |

</details>

### Switch Schedules

<details>

Switches support being open/closed via schedules. They can either be provided
per-phase or as a single balanced value.

For any timepoints where the status values are not specified, the switch will be
assumed to be in its default open/closed state.

#### Balanced Schedule
| Variable Name | Description                                          | Units |
|---------------|------------------------------------------------------|-------|
| status        | either 0 (indicates open) or 1 (indicates closed)    | n/a   |

#### Unbalanced Schedule
| Variable Name | Description                                          | Units |
|---------------|------------------------------------------------------|-------|
| status_a      | either 0 (indicates open) or 1 (indicates closed)    | n/a   |
| status_b      | either 0 (indicates open) or 1 (indicates closed)    | n/a   |
| status_c      | either 0 (indicates open) or 1 (indicates closed)    | n/a   |

</details>

### Energy Source / Slack Schedules

<details>

Energy Sources support a balanced operating voltage schedule.

For any timepoints where the operationg voltage values are not specified, the
energy source will be assumed to use its default operating voltage.
#### Operating Voltage Schedule
| Variable Name     | Description                                      | Units |
|-------------------|--------------------------------------------------|-------|
| operating_voltage | operating voltage (per unit value; >0.4, <1.6)   | p.u   |

</details>

### Equivalent Substation Schedules

<details>

Equivalent substations support a balanced or unbalanced PQ schedule.

For any timepoints where the PQ values are not specified, P,Q are assumed to be 0.

#### Balanced Schedule
| Variable Name | Description                                                       | Units |
|---------------|-------------------------------------------------------------------|-------|
| p             | real power (positive=consumption, negative=backfeeding            | W     |
| q             | reactive power (positive=consumption, negative=backfeeding)       | VAR   |

#### Unbalanced Schedule
| Variable Name | Description                                                            | Units |
|---------------|------------------------------------------------------------------------|-------|
| timestamp     | UTC timestamp in ISO8601 format (e.g., 2019-09-04T00:00:00+00:00)      | n/a   |
| p_a           | real power on A phase (positive=consumption, negative=backfeeding      | W     |
| p_b           | real power on B phase (positive=consumption, negative=backfeeding      | W     |
| p_c           | real power on C phase (positive=consumption, negative=backfeeding      | W     |
| q_a           | reactive power on A phase (positive=consumption, negative=backfeeding) | VAR   |
| q_b           | reactive power on B phase (positive=consumption, negative=backfeeding) | VAR   |
| q_c           | reactive power on C phase (positive=consumption, negative=backfeeding) | VAR   |

</details>

### Transformer/Regulator Schedules

<details>

Transformers and regulators support a balanced or unbalanced tap position schedule.

For any timepoints where the tap position values are not specified, the transformer will be
assumed to be in its default tap position.

#### Balanced Schedule
| Column Name     | Description                                        | Units |
|-----------------|----------------------------------------------------|-------|
| tap_positions   | integer number indicating the tap position         | n/a   |

#### Unbalanced Schedule
| Column Name     | Description                                           | Units |
|-----------------|-------------------------------------------------------|-------|
| tap_positions_a | integer number indicating the tap position on phase a | n/a   |
| tap_positions_b | integer number indicating the tap position on phase b | n/a   |
| tap_positions_c | integer number indicating the tap position on phase c | n/a   |

</details>
