import json
from pathlib import Path


def test_playwright_config_initializes_node_path():
    """Verify that playwright.config.ts has cross-directory Node resolution logic."""
    root = Path(__file__).resolve().parents[2]
    config_path = root / "web" / "playwright.config.ts"
    assert config_path.is_file(), "web/playwright.config.ts must exist"
    content = config_path.read_text(encoding="utf-8")
    assert "webNodeModules" in content
    assert "_initPaths" in content
    assert 'testDir: "../tests/e2e"' in content


def test_package_json_e2e_script_sets_node_path():
    """Verify that web/package.json test:e2e script includes NODE_PATH."""
    root = Path(__file__).resolve().parents[2]
    package_json_path = root / "web" / "package.json"
    assert package_json_path.is_file(), "web/package.json must exist"
    data = json.loads(package_json_path.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {})
    e2e_cmd = scripts.get("test:e2e", "")
    assert "NODE_PATH=node_modules" in e2e_cmd
    assert "playwright test" in e2e_cmd


def test_ci_workflow_has_discovery_guard_and_node_path():
    """Verify that .github/workflows/ci.yml runs a discovery check and passes NODE_PATH."""
    root = Path(__file__).resolve().parents[2]
    ci_path = root / ".github" / "workflows" / "ci.yml"
    assert ci_path.is_file(), ".github/workflows/ci.yml must exist"
    content = ci_path.read_text(encoding="utf-8")
    assert "Verify Playwright Test Discovery" in content
    assert "test:e2e -- --list" in content
    assert "NODE_PATH: web/node_modules" in content
