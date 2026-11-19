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
