"""Generative plain-language summarization of structured incidents and proposals.

Pure template engine as reliable default with optional external LLM wrapper.
The LLM never makes decisions, never validates feasibility, and never approves anything.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from core.metrics import summaries_total, summary_fallback_total

logger = logging.getLogger("fuel_simulator.core.summarize")


class TemplateSummarizer:
    """Fast, deterministic, zero-dependency summarizer for operational entities."""

    def summarize_incident(self, incident: dict[str, Any]) -> str:
        inc_type = str(incident.get("type", "unknown")).lower()
        severity = str(incident.get("severity", "info")).upper()
        detail = incident.get("detail", {})
        if isinstance(detail, str):
            import json

            try:
                detail = json.loads(detail)
            except Exception:
                detail = {}

        evidence = detail.get("evidence", {})

        if inc_type == "calibration_drift":
            st_id = evidence.get("station_id", detail.get("entity_id", "station"))
            fuel = evidence.get("fuel_type", "fuel")
            direction = evidence.get("direction", "SURGE")
            ratio = evidence.get("mean_ratio", "1.3")
            ticks = evidence.get("consecutive_ticks", 4)
            return (
                f"[{severity}] Forecast calibration for {st_id} ({fuel}) has drifted {direction} "
                f"with a mean ratio of {ratio}× over {ticks} consecutive ticks. "
                "Recalibration in progress; demand variance exceeds normal envelope [0.8, 1.25]."
            )

        if inc_type == "demand_anomaly":
            st_id = evidence.get("station_id", detail.get("entity_id", "station"))
            fuel = evidence.get("fuel_type", "fuel")
            ratio = evidence.get("ratio", "elevated")
            return (
                f"[{severity}] Sustained consumption surge detected at {st_id} for {fuel} "
                f"({ratio}× baseline). Tank inventory depleting faster than scheduled diurnal rate."
            )

        if inc_type == "stockout_risk":
            st_id = detail.get("station_id", "station")
            fuel = detail.get("fuel_type", "fuel")
            risk = detail.get("risk_level", severity).upper()
            return (
                f"[{severity}] Elevated stockout risk ({risk}) at {st_id} for {fuel}. "
                "Urgent replenishment required to prevent unserved demand within next 24 hours."
            )

        if inc_type == "bottleneck":
            entity = detail.get("entity_id", "depot")
            util = evidence.get("utilization")
            if util is not None:
                pct = round(float(util) * 100, 1)
                return (
                    f"[{severity}] Dispatch bottleneck at {entity}. Rack utilization is at {pct}%, "
                    "approaching max daily throughput limit."
                )
            return (
                f"[{severity}] Supply bottleneck detected at {entity}. Net 24-hour forward cover "
                "is in deficit relative to downstream station demand."
            )

        if inc_type == "emerging_regional_disruption":
            reg = evidence.get("region_id", "corridor")
            routes = evidence.get("disrupted_routes", [])
            r_str = ", ".join(routes) if routes else "multiple routes"
            return (
                f"[{severity}] Regional transit disruption in {reg}. Blocked corridors: {r_str}. "
                "Alternative dispatch routes must be prioritized."
            )

        explanation = detail.get("explanation")
        if explanation:
            return f"[{severity}] {explanation}"
        ent = detail.get("entity_id", "unknown")
        return f"[{severity}] Incident {inc_type} detected on entity {ent}."

    def summarize_recommendation(self, recommendation: dict[str, Any]) -> str:
        req = recommendation.get("request_body", {})
        qty = req.get("quantity", recommendation.get("quantity", 0))
        fuel = req.get("fuel_type", recommendation.get("fuel_type", "fuel"))
        src = req.get("source_depot_id", recommendation.get("depot_id", "depot"))
        dst = req.get("destination_station_id", recommendation.get("station_id", "station"))
        route = req.get("route_id", recommendation.get("route_id", "route"))

        expl = recommendation.get("explanation_json", {})
        before = expl.get("risk_before", {})
        after = expl.get("risk_after", {})
        h_before = before.get("hours_to_stockout")
        h_after = after.get("hours_to_stockout")
        hb_str = f"{h_before:.1f}h" if isinstance(h_before, (int, float)) else ">24h"
        ha_str = f"{h_after:.1f}h" if isinstance(h_after, (int, float)) else ">24h"

        return (
            f"Proposed Allocation: Dispatch {qty:,.0f} L of {fuel} from {src} to {dst} via "
            f"{route}. Expected to improve stockout runway from {hb_str} to {ha_str}."
        )


class LLMSummarizer:
    """Optional LLM summarizer with strict timeout and fallback to TemplateSummarizer."""

    def __init__(
        self,
        api_key: str | None = None,
        timeout_seconds: float = 3.0,
        enabled: bool = False,
    ) -> None:
        self.api_key = api_key or os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.timeout_seconds = timeout_seconds
        self.enabled = (
            enabled or os.getenv("ENABLE_LLM_SUMMARIZER", "false").lower() == "true"
        ) and bool(self.api_key)
        self.fallback = TemplateSummarizer()

    def summarize_incident(self, incident: dict[str, Any]) -> tuple[str, str]:
        """Return (summary_text, source) where source is 'llm' or 'template'."""
        if not self.enabled or not self.api_key:
            summaries_total.labels(source="template").inc()
            return self.fallback.summarize_incident(incident), "template"

        try:
            # Short, bounded call with 3 second timeout
            # If mock or simulated or remote, call LLM endpoint
            # For resilience and test safety without external API egress, verify timeout & fallback
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.post(
                    "https://api.example.com/v1/summarize",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"incident": incident},
                )
                if res.status_code == 200:
                    summaries_total.labels(source="llm").inc()
                    return res.json().get("summary", ""), "llm"
                raise RuntimeError(f"LLM API returned {res.status_code}")
        except Exception as exc:
            logger.info("LLM summarizer failed (%s); falling back to template", type(exc).__name__)
            summary_fallback_total.inc()
            summaries_total.labels(source="template").inc()
            return self.fallback.summarize_incident(incident), "template"
