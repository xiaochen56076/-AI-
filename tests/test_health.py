import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_envelope_and_request_id():
    client = APIClient()
    response = client.get("/api/v1/health", HTTP_X_REQUEST_ID="trace-demo-001")

    assert response.status_code == 200
    assert response["X-Request-ID"] == "trace-demo-001"
    assert response.json() == {
        "code": 0,
        "message": "操作成功",
        "data": {
            "status": "ok",
            "service": "CampusHub API",
            "time": response.json()["data"]["time"],
        },
        "request_id": "trace-demo-001",
    }


@pytest.mark.django_db
def test_not_found_uses_envelope():
    response = APIClient().get("/api/v1/not-exists")
    assert response.status_code == 404
    assert response.json()["code"] == 10002
    assert response.json()["request_id"]
