import os
import tempfile

import pytest


@pytest.fixture()
def client():
    import app as module

    # Create a temporary directory for this test's database.
    temp_dir = tempfile.TemporaryDirectory()
    path = os.path.join(temp_dir.name, "test_irrigation.db")

    original_database = module.DATABASE
    original_testing = module.app.config.get("TESTING", False)

    module.DATABASE = path
    module.app.config.update(TESTING=True)
    module.init_db()

    try:
        with module.app.test_client() as test_client:
            yield test_client
    finally:
        module.DATABASE = original_database
        module.app.config.update(TESTING=original_testing)

        # TemporaryDirectory cleans up the test database directory.
        # Ignore a Windows cleanup error rather than failing the tests.
        try:
            temp_dir.cleanup()
        except PermissionError:
            pass


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_three_zones(client):
    response = client.get("/api/zones")
    assert response.status_code == 200
    assert len(response.json) == 3


def test_invalid_threshold(client):
    response = client.patch("/api/zones/1", json={"threshold": 100})
    assert response.status_code == 400


def test_iot_reading(client):
    response = client.post(
        "/api/iot/readings",
        json={"zone_id": 1, "moisture": 25, "temperature": 24},
    )
    assert response.status_code == 201
    assert response.json["moisture"] == 25