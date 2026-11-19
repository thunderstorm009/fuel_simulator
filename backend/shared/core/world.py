"""Fixed demand profiles and inclusive hourly factors from the simulator guide."""

from __future__ import annotations

from datetime import datetime

DAILY_LITERS: dict[str, dict[str, float]] = {
    "urban_high": {"DIESEL": 8500, "PETROL": 10500, "OCTANE": 5600},
    "industrial": {"DIESEL": 14000, "PETROL": 4500, "OCTANE": 2200},
    "highway": {"DIESEL": 10500, "PETROL": 11000, "OCTANE": 6200},
    "regional": {"DIESEL": 7200, "PETROL": 7600, "OCTANE": 3600},
}

PROFILE_NOISE: dict[str, float] = {
    "urban_high": 0.10,
    "industrial": 0.08,
    "highway": 0.12,
    "regional": 0.10,
}


def hour_factor(profile: str, sim_time: datetime) -> float:
    hour = sim_time.hour
    if profile == "industrial":
        return 1.55 if 6 <= hour <= 17 else 0.45
    if profile == "highway":
        return 1.35 if 6 <= hour <= 9 or 16 <= hour <= 20 else 0.75
    if profile == "urban_high":
        return 1.45 if 7 <= hour <= 9 or 16 <= hour <= 20 else 0.70
    if profile == "regional":
        return 1.25 if 7 <= hour <= 20 else 0.65
    raise ValueError(f"unknown demand profile: {profile}")
