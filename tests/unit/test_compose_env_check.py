from __future__ import annotations

import json

from scripts.check_compose_env import configuration_errors, load_compose_config


def compose_config(*, database_password: str, url_password: str, predictor_port: int) -> dict:
    return {
        "services": {
            "postgres": {
                "environment": {
                    "POSTGRES_USER": "fuel",
                    "POSTGRES_PASSWORD": database_password,
                    "POSTGRES_DB": "fuel",
                }
            },
            "api": {
                "environment": {
                    "DATABASE_URL": f"postgresql://fuel:{url_password}@postgres:5432/fuel"
                }
            },
            "worker": {
                "environment": {
                    "DATABASE_URL": f"postgresql://fuel:{url_password}@postgres:5432/fuel",
                    "PREDICTOR_URL": f"http://predictor:{predictor_port}",
                }
            },
            "predictor": {"ports": [{"target": 8103, "published": 8103, "protocol": "tcp"}]},
        }
    }


def test_compose_environment_accepts_matching_database_and_predictor_config() -> None:
    assert (
        configuration_errors(
            compose_config(
                database_password="fuel-local", url_password="fuel-local", predictor_port=8103
            )
        )
        == []
    )


def test_compose_environment_reports_mismatches_without_secret_values() -> None:
    errors = configuration_errors(
        compose_config(
            database_password="db-secret", url_password="url-secret", predictor_port=8100
        )
    )

    assert len(errors) == 3
    assert all("secret" not in error for error in errors)


def test_compose_environment_can_validate_clean_clone_env_file(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env.example"
    env_file.write_text("safe example config")
    expected = compose_config(
        database_password="fuel-local", url_password="fuel-local", predictor_port=8103
    )

    class Result:
        stdout = json.dumps(expected)

    def run(command, **kwargs):
        assert command == [
            "docker",
            "compose",
            "--env-file",
            str(env_file),
            "config",
            "--format",
            "json",
        ]
        return Result()

    monkeypatch.setattr("scripts.check_compose_env.subprocess.run", run)
    assert load_compose_config(env_file) == expected
