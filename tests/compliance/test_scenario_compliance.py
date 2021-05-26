from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from idp_schedule_provider.forecaster.controller import insert_scenarios
from idp_schedule_provider.forecaster.models import Scenarios


def test_get_scenarios_none(test_client: TestClient):
    response = test_client.get("/scenario")
    assert response.status_code == 200
    assert response.json() == {"scenarios": {}}


def test_get_scenarios_many(test_client: TestClient, database_client: Session):
    insert_scenarios(
        database_client,
        [
            Scenarios(id="sce1", name="Scenario 1", description="Test Scenario 1"),
            Scenarios(id="sce2", name="Scenario 2"),
        ],
    )

    response = test_client.get("/scenario")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["scenarios"]["sce1"] == {
        "name": "Scenario 1",
        "description": "Test Scenario 1",
    }
    assert response_data["scenarios"]["sce2"] == {"name": "Scenario 2", "description": None}
