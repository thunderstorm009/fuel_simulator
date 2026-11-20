import respx
from api.main import app
from fastapi.testclient import TestClient
from httpx import Response


@respx.mock
def test_forecast_chaos_requires_token_and_forwards_switch(monkeypatch) -> None:
    monkeypatch.setenv("OPERATOR_TOKEN", "test-operator")
    monkeypatch.setenv("PREDICTOR_URL", "http://predictor.test")
    forwarded = respx.post("http://predictor.test/admin/fail").mock(
        return_value=Response(200, json={"enabled": True})
    )

    with TestClient(app) as client:
        denied = client.post("/api/chaos/forecast-fail", json={"enabled": True})
        enabled = client.post(
            "/api/chaos/forecast-fail",
            json={"enabled": True},
            headers={"X-Operator-Token": "test-operator"},
        )

    assert denied.status_code == 401
    assert enabled.status_code == 200
    assert enabled.json() == {"enabled": True, "simulated": True}
    assert forwarded.call_count == 1
