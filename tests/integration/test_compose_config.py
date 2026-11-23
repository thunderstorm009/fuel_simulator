import json
import os
import subprocess


def test_frontend_host_port_can_be_overridden() -> None:
    environment = os.environ.copy()
    environment["FRONTEND_HOST_PORT"] = "5174"
    result = subprocess.run(
        ["docker", "compose", "config", "--format", "json"],
        check=True,
        capture_output=True,
        env=environment,
        text=True,
    )
    config = json.loads(result.stdout)
    assert config["services"]["frontend"]["ports"][0]["published"] == "5174"


def test_alerts_profile_is_isolated_from_default_stack() -> None:
    # 1. Default config must not include alertmanager or webhook-receiver
    res_default = subprocess.run(
        ["docker", "compose", "config", "--services"],
        check=True,
        capture_output=True,
        text=True,
    )
    default_services = set(res_default.stdout.strip().split())
    assert "alertmanager" not in default_services
    assert "webhook-receiver" not in default_services
    assert "api" in default_services
    assert "worker" in default_services

    # 2. Config with --profile alerts includes both
    res_alerts = subprocess.run(
        ["docker", "compose", "--profile", "alerts", "config", "--services"],
        check=True,
        capture_output=True,
        text=True,
    )
    alert_services = set(res_alerts.stdout.strip().split())
    assert "alertmanager" in alert_services
    assert "webhook-receiver" in alert_services
