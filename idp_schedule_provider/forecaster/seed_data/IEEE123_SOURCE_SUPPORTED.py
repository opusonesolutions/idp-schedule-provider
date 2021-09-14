from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta

from idp_schedule_provider.forecaster.models import ForecastData, Scenarios

scenario_id = "56789"
scenarios = [
    Scenarios(
        id=scenario_id,
        name="IEEE123_EXTERNAL_SCHEDULES Supported",
        description="Scenario Data for the IEEE123_EXTERNAL_SCHEDULES workspace \
            with supported assets",
    ),
]

forecast_data = [
    # feeder
    *[
        ForecastData(
            scenario_id=scenario_id,
            asset_name="_33D6B389-2A6F-4BA9-8C50-6A342146F87D",
            feeder="_33D6B389-2A6F-4BA9-8C50-6A342146F87D",
            data={
                "load": 2.5e6 + 0.1e6 * i,
                "load_pf": 0.9,
                "generation": 2.5e3 + 0.1e3 * i,
                "generation_pf": 0.9,
            },
            timestamp=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc) + relativedelta(hours=i),
        )
        for i in range(0, 24)
    ],
    # sync machine
    *[
        ForecastData(
            scenario_id=scenario_id,
            asset_name="_6b6586f6-4b22-4523-a568-96f8ac0434c4",
            feeder="_33D6B389-2A6F-4BA9-8C50-6A342146F87D",
            data={"p": 500 + 50 * i, "q": 50 + 50 * i},
            timestamp=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc) + relativedelta(hours=i),
        )
        for i in range(0, 24)
    ],
    # pv
    *[
        ForecastData(
            scenario_id=scenario_id,
            asset_name="_0a8deb74-98ff-4a63-a403-4dab07202e8c",
            feeder="_33D6B389-2A6F-4BA9-8C50-6A342146F87D",
            data={"p": 250 + 50 * i, "q": 25 + 50 * i},
            timestamp=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc) + relativedelta(hours=i),
        )
        for i in range(0, 24)
    ],
    # ev
    # *[
    #     ForecastData(
    #         scenario_id=scenario_id,
    #         asset_name="_422cdbd8-684d-4416-8604-b056f7470d95",
    #         feeder="_33D6B389-2A6F-4BA9-8C50-6A342146F87D",
    #         data={"p": 375 + 50 * i, "q": 37.5 + 50 * i},
    #         timestamp=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc) + relativedelta(hours=i),
    #     )
    #     for i in range(0, 24)
    # ],
    # ev2 (charging events)
    # TODO: EV Support
    # *[ForecastData(
    #     scenario_id=scenario_id,
    #     asset_name="_422cdbd8-684d-4416-8604-b056f7470d95",
    #     feeder="_33D6B389-2A6F-4BA9-8C50-6A342146F87D",
    #     data={"p": 25, "q": 25},
    #     timestamp=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc) + relativedelta(hours=i),
    # ) for i in range(0, 24)],
    # bess
    # *[
    #     ForecastData(
    #         scenario_id=scenario_id,
    #         asset_name="_606f79ad-de7c-49cb-b73b-f9a1eba13aeb",
    #         feeder="_33D6B389-2A6F-4BA9-8C50-6A342146F87D",
    #         data={"p": 750 * 25 + i, "q": 75 + 50 * i},
    #         timestamp=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc) + relativedelta(hours=i),
    #     )
    #     for i in range(0, 24)
    # ],
    # # bess2 (SoC)
    # *[
    #     ForecastData(
    #         scenario_id=scenario_id,
    #         asset_name="_234d2177-5111-4586-b82a-d36db6286ffc",
    #         feeder="_33D6B389-2A6F-4BA9-8C50-6A342146F87D",
    #         data={"min_SOC": 5 + i, "max_SOC": 95 - i},
    #         timestamp=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc) + relativedelta(hours=i),
    #     )
    #     for i in range(0, 24)
    # ],
    # # capacitor
    # *[
    #     ForecastData(
    #         scenario_id=scenario_id,
    #         asset_name="_0B407ED4-9A66-4607-814F-A92BB8D7B1F0",
    #         feeder="_33D6B389-2A6F-4BA9-8C50-6A342146F87D",
    #         data={"state": i % 2},
    #         timestamp=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc) + relativedelta(hours=i),
    #     )
    #     for i in range(0, 24)
    # ],
    # load
    *[
        ForecastData(
            scenario_id=scenario_id,
            asset_name="_C9D39F32-CA4C-4471-AB9E-797400490385",
            feeder="_33D6B389-2A6F-4BA9-8C50-6A342146F87D",
            data={"p": 250 + 50 * i, "q": 25 + 50 * i},
            timestamp=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc) + relativedelta(hours=i),
        )
        for i in range(0, 24)
    ],
    # # switch
    # *[
    #     ForecastData(
    #         scenario_id=scenario_id,
    #         asset_name="_84C331E2-2156-4820-934A-581EE6D4DFBC",
    #         feeder="_33D6B389-2A6F-4BA9-8C50-6A342146F87D",
    #         data={"status": {"A": i % 2, "B": (i + 2) % 2, "C": i % 2}},
    #         timestamp=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc) + relativedelta(hours=i),
    #     )
    #     for i in range(0, 24)
    # ],
    # not a valid set of variables/assets
    *[
        ForecastData(
            scenario_id=scenario_id,
            asset_name="_fbfb",
            feeder="_33D6B389-2A6F-4BA9-8C50-6A342146F87D",
            data={"something": 25, "status": {"A": 1, "B": 0, "C": 1}},
            timestamp=datetime(2000, 1, 1, 0, 0, 0, 0, timezone.utc) + relativedelta(hours=i),
        )
        for i in range(0, 24)
    ],
]
