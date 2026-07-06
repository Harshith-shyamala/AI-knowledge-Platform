from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def test_portfolio_validation_script_passes() -> None:
    project_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(project_root / "scripts" / "validate_portfolio.py")],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "Portfolio validation passed." in result.stdout


def test_load_test_summary_reports_percentiles() -> None:
    project_root = Path(__file__).resolve().parents[3]
    module_path = project_root / "scripts" / "load_test_api.py"
    spec = importlib.util.spec_from_file_location("load_test_api", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["load_test_api"] = module
    spec.loader.exec_module(module)

    measurements = [
        module.Measurement(name="search", status_code=200, latency_ms=10.0),
        module.Measurement(name="search", status_code=200, latency_ms=20.0),
        module.Measurement(name="search", status_code=200, latency_ms=30.0),
        module.Measurement(name="chat", status_code=200, latency_ms=40.0),
    ]

    summary = module._summary(measurements)

    assert summary["search"]["count"] == 3
    assert summary["search"]["status_codes"] == [200]
    assert summary["search"]["p50_ms"] > 0
    assert summary["search"]["p95_ms"] >= summary["search"]["p50_ms"]
    assert summary["chat"]["max_ms"] == 40.0
