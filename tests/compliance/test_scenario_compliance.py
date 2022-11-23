from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session

from idp_schedule_provider.forecaster.controller import insert_rows
from idp_schedule_provider.forecaster.models import Scenarios


def test_get_scenarios_none(test_client: TestClient):
    response = test_client.get("/scenarios")
    assert response.status_code == 200
    assert response.json() == {"scenarios": {}}


def test_get_scenarios_many(test_client: TestClient, database_client: Session):
    insert_rows(
        database_client,
        [
            Scenarios(id="sce1", name="Scenario 1", description="Test Scenario 1"),
            Scenarios(id="sce2", name="Scenario 2"),
        ],
    )

    response = test_client.get("/scenarios")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["scenarios"]["sce1"] == {
        "name": "Scenario 1",
        "description": "Test Scenario 1",
    }
    assert response_data["scenarios"]["sce2"] == {"name": "Scenario 2", "description": None}


def test_update_scenarios_success(test_client: TestClient, database_client: Session):
    insert_rows(
        database_client,
        [
            Scenarios(id="sce1", name="Scenario 1", description="Test Scenario 1"),
        ],
    )

    response = test_client.put(
        "/scenario/sce1",
        json={"name": "Updated scneario name", "description": "Updated description"},
    )
    assert response.status_code == 204


def test_update_scenarios_name_exists(test_client: TestClient, database_client: Session):
    insert_rows(
        database_client,
        [
            Scenarios(id="sce1", name="Scenario 1", description="Test Scenario 1"),
            Scenarios(id="sce2", name="Scenario 2", description="Test Scenario 1"),
        ],
    )

    response = test_client.put(
        "/scenario/sce1", json={"name": "Scenario 2", "description": "Updated description"}
    )
    assert response.status_code == 409


def test_update_scenarios_create_scenarios_if_not_exists(
    test_client: TestClient, database_client: Session
):

    response = test_client.put(
        "/scenario/sce1",
        json={"name": "New Scenario", "description": "Scenario description"},
    )
    assert response.status_code == 204


def test_update_scenarios_create_scenarios_with_existing_name(
    test_client: TestClient, database_client: Session
):
    insert_rows(
        database_client,
        [
            Scenarios(id="sce1", name="Scenario", description="Test Scenario 1"),
        ],
    )
    response = test_client.put(
        "/scenario/sce2",
        json={"name": "Scenario", "description": "Scenario description"},
    )
    assert response.status_code == 409


def test_update_scenarios_description_only(test_client: TestClient, database_client: Session):
    insert_rows(
        database_client,
        [
            Scenarios(id="sce1", name="Scenario", description="Test Scenario 1"),
        ],
    )
    response = test_client.put(
        "/scenario/sce1",
        json={"name": "Scenario", "description": "Scenario description"},
    )
    assert response.status_code == 204
