from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

from core.summarize import LLMSummarizer, TemplateSummarizer


def test_template_summarizer_incident_types() -> None:
    summarizer = TemplateSummarizer()

    # 1. Calibration drift
    drift_inc = {
        "id": 1,
        "type": "calibration_drift",
        "severity": "warning",
        "detail": {
            "entity_id": "station-north",
            "evidence": {
                "station_id": "station-north",
                "fuel_type": "regular",
                "direction": "SURGE",
                "mean_ratio": "1.35",
                "consecutive_ticks": 5,
            },
        },
    }
    s1 = summarizer.summarize_incident(drift_inc)
    assert "[WARNING]" in s1
    assert "station-north" in s1
    assert "1.35×" in s1

    # 2. Demand anomaly
    anomaly_inc = {
        "id": 2,
        "type": "demand_anomaly",
        "severity": "high",
        "detail": {
            "entity_id": "station-south",
            "evidence": {"station_id": "station-south", "fuel_type": "diesel", "ratio": "1.8"},
        },
    }
    s2 = summarizer.summarize_incident(anomaly_inc)
    assert "[HIGH]" in s2
    assert "station-south" in s2
    assert "1.8× baseline" in s2

    # 3. Stockout risk
    risk_inc = {
        "id": 3,
        "type": "stockout_risk",
        "severity": "critical",
        "detail": {"station_id": "station-east", "fuel_type": "regular", "risk_level": "critical"},
    }
    s3 = summarizer.summarize_incident(risk_inc)
    assert "[CRITICAL]" in s3
    assert "station-east" in s3

    # 4. Bottleneck
    bottle_inc = {
        "id": 4,
        "type": "bottleneck",
        "severity": "warning",
        "detail": {"entity_id": "depot-alpha", "evidence": {"utilization": 0.95}},
    }
    s4 = summarizer.summarize_incident(bottle_inc)
    assert "[WARNING]" in s4
    assert "95.0%" in s4

    # 5. Recommendation summary
    rec = {
        "request_body": {
            "quantity": 10000,
            "fuel_type": "regular",
            "source_depot_id": "depot-alpha",
            "destination_station_id": "station-east",
            "route_id": "route-alpha-east",
        },
        "explanation_json": {
            "risk_before": {"hours_to_stockout": 2.5},
            "risk_after": {"hours_to_stockout": 8.0},
        },
    }
    rec_sum = summarizer.summarize_recommendation(rec)
    assert "10,000" in rec_sum
    assert "depot-alpha" in rec_sum
    assert "station-east" in rec_sum
    assert "2.5h to 8.0h" in rec_sum


def test_llm_summarizer_disabled_falls_back_to_template() -> None:
    summarizer = LLMSummarizer(enabled=False)
    incident = {
        "id": 10,
        "type": "stockout_risk",
        "severity": "critical",
        "detail": {"station_id": "station-1", "fuel_type": "regular"},
    }
    summary, source = summarizer.summarize_incident(incident)
    assert source == "template"
    assert "station-1" in summary


def test_llm_summarizer_error_falls_back_without_logging_secrets(
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret_key = "test-operator-api-key-xyz"
    summarizer = LLMSummarizer(api_key=secret_key, enabled=True)

    incident = {
        "id": 11,
        "type": "stockout_risk",
        "severity": "high",
        "detail": {"station_id": "station-2", "fuel_type": "diesel"},
    }

    # Simulate network error
    with patch("httpx.Client.post", side_effect=Exception("Connection timed out")):
        with caplog.at_level(logging.INFO):
            summary, source = summarizer.summarize_incident(incident)

    assert source == "template"
    assert "station-2" in summary
    # Assert secret key is NEVER printed in any logs
    assert secret_key not in caplog.text
