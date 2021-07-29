Gets the asset schedule data for a single asset or all assets.

## Use Case
This single asset version of this API will be used for the following
* Displaying graphs in the user interface

The many asset version of this API will be used for the following
* Loading schedule data for analysis

## Schedule Variables

### Feeder / Substation Schedules

<details>
Feeders and substations support a balanced load/gen schedules.

#### Load/Gen Schedule
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

| Variable Name | Description                                          | Units |
|---------------|------------------------------------------------------|-------|
| p             | real power consumption                               | W     |
| q             | reactive power consumption                           | VAR   |


#### Charging Event Schedule
A charging event schedule will be used for an EV when it is in *Global* mode and performing an OPF. 
When in this mode the optimization engine will make use of the provided events to determine how to
optimally charge the electric vehicle to meet the desired objective.

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

| Variable Name | Description                                                       | Units |
|---------------|-------------------------------------------------------------------|-------|
| p             | real power (positive = charging, negative = discharging)          | W     |
| q             | reactive power (positive = charging, negative = discharging)      | VAR   |

#### Soc Schedule
A SoC schedule will be used for a BESS if it is in global mode. The optimization will control
the PQ of the battery to optimally dispatch and the SoC schedule will be used to cap the
min and max charge levels.

| Variable Name | Description                                          | Units |
|---------------|------------------------------------------------------|-------|
| min_SOC       | value between 0 and 1  (where 0 = 0% and 1 = 100%)   | %     |
| max_SOC       | value between 0 and 1  (where 0 = 0% and 1 = 100%)   | %     |

</details>

### Capacitor/Reactor Schedules

<details>

Capacitors support being connected and disconnected via schedules. This can either be provided
per-phase or as a single balanced value.

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

Synchronous machines and their variations support a balanced PQ schedule

#### Balanced Schedule
| Variable Name | Description                                          | Units |
|---------------|------------------------------------------------------|-------|
| p             | real power generation                                | W     |
| q             | reactive power generation                            | VAR   |

</details>

### Asynchronous Machine / Wind Schedules

<details>

Asynchronous machines and their variations support a balanced PQ schedule

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

#### Operating Voltage Schedule
| Variable Name     | Description                                      | Units |
|-------------------|--------------------------------------------------|-------|
| operating_voltage | operating voltage (per unit value; >0.4, <1.6)   | p.u   |

</details>

### Equivalent Substation Schedules

<details>

Equivalent substations support a balanced or unbalanced PQ schedule.

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

Transformers and regulators support a balanced or unbalanced tap position schedule

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
