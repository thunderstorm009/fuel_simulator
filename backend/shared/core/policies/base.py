"""Policy contracts and candidate plan records."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from core.models import AllocationTerms, Snapshot
from core.risk import ForecastRecord


@dataclass(frozen=True)
class PolicyPlan:
    request: AllocationTerms
    stockout_hours: float | None
    arrival_tick: int
    projected_inventory_at_arrival: float
    target_inventory: float
    constraints_applied: list[dict[str, object]] = field(default_factory=list)
    alternatives: list[dict[str, object]] = field(default_factory=list)


class Policy(Protocol):
    name: str

    def recommend(
        self, snapshot: Snapshot, forecasts: Sequence[ForecastRecord]
    ) -> list[PolicyPlan]: ...
