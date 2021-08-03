from datetime import datetime, timezone

from idp_schedule_provider.forecaster.models import ForecastData, Scenarios

scenarios = [
    Scenarios(id="sce1", name="Scenario 1", description="Test Scenario 1"),
    Scenarios(id="sce2", name="Scenario 2", description="Test Scenario 2"),
]

forecast_data = []
# seeds 1 year of data for 3 assets on scenario1. no data on scenario 2
for asset in ["asset_1", "asset_2", "asset_3"]:
    for month in range(1, 13):
        for day in range(1, 29):  # 28 days for now
            for hour in range(24):
                timestamp = datetime(2000, month, day, hour, 0, 0, 0, timezone.utc)
                forecast_data.append(
                    ForecastData(
                        scenario_id="sce1",
                        asset_name=asset,
                        feeder="f1",
                        data={
                            "p": hour,
                            "q": {"A": hour, "B": day},
                        },
                        timestamp=timestamp,
                    )
                )
