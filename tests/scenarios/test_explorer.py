from pathlib import Path

from scripts.explore_sim import sample_path


def test_sample_path_preserves_single_json_suffix(tmp_path: Path) -> None:
    assert sample_path("step-01.json", tmp_path) == tmp_path / "step-01.json"
    assert sample_path("instance", tmp_path) == tmp_path / "instance.json"
