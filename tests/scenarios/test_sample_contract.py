import json
from pathlib import Path

import pytest

from core.models import (
    Allocation,
    DemandObs,
    Depot,
    Instance,
    Metrics,
    Region,
    Route,
    SimEvent,
    Station,
    SupplyArrival,
)

SAMPLES = Path(__file__).parents[2] / "docs" / "sim-samples"


@pytest.mark.parametrize(
    ("sample", "model", "is_list"),
    [
        ("instance", Instance, False),
        ("regions", Region, True),
        ("depots", Depot, True),
        ("depot-detail", Depot, False),
        ("stations", Station, True),
        ("routes", Route, True),
        ("supply-arrivals", SupplyArrival, True),
        ("events", SimEvent, True),
        ("allocations", Allocation, True),
        ("allocation-pending", Allocation, False),
        ("demand-history", DemandObs, True),
        ("metrics", Metrics, False),
    ],
)
def test_documented_json_samples_parse(sample: str, model: type, is_list: bool) -> None:
    data = json.loads((SAMPLES / f"{sample}.json").read_text())
    rows = data if is_list else [data]
    assert rows
    for row in rows:
        model.model_validate(row)


def test_every_sample_file_is_valid_json() -> None:
    for path in SAMPLES.glob("*.json"):
        json.loads(path.read_text())
