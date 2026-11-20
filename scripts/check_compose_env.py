"""Validate resolved Compose credentials without displaying secret values."""

from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any
from urllib.parse import urlsplit


def configuration_errors(config: dict[str, Any]) -> list[str]:
    services = config.get("services", {})
    postgres = services.get("postgres", {}).get("environment", {})
    expected_user = str(postgres.get("POSTGRES_USER", ""))
    expected_password = str(postgres.get("POSTGRES_PASSWORD", ""))
    expected_database = str(postgres.get("POSTGRES_DB", ""))
    errors: list[str] = []

    for service_name in ("api", "worker"):
        environment = services.get(service_name, {}).get("environment", {})
        raw_url = str(environment.get("DATABASE_URL", ""))
        parsed = urlsplit(raw_url)
        if (
            parsed.scheme not in {"postgres", "postgresql"}
            or parsed.username != expected_user
            or parsed.password != expected_password
            or parsed.path.lstrip("/") != expected_database
        ):
            errors.append(
                f"{service_name}.DATABASE_URL credentials/database do not match "
                "the postgres service"
            )

    predictor_url = urlsplit(
        str(services.get("worker", {}).get("environment", {}).get("PREDICTOR_URL", ""))
    )
    port_bindings = services.get("predictor", {}).get("ports", [])
    predictor_service_port = next(
        (
            int(binding["target"])
            for binding in port_bindings
            if isinstance(binding, dict) and binding.get("target") is not None
        ),
        None,
    )
    if predictor_url.hostname != "predictor" or predictor_url.port != predictor_service_port:
        errors.append("worker.PREDICTOR_URL must target the predictor service on its internal port")
    return errors


def load_compose_config(env_file: str | None = None) -> dict[str, Any]:
    command = ["docker", "compose"]
    if env_file:
        command.extend(["--env-file", str(env_file)])
    command.extend(["config", "--format", "json"])
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", help="Compose interpolation file to validate")
    args = parser.parse_args()
    try:
        config = load_compose_config(args.env_file)
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        print("FAIL: could not resolve the Docker Compose configuration")
        return 1

    errors = configuration_errors(config)
    if errors:
        for error in errors:
            print(f"FAIL: {error}; values are redacted")
        return 1
    print("PASS: database credentials and predictor URL match Compose services")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
