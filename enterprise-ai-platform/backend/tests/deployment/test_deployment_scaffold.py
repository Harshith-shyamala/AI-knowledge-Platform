from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_deployment_scaffold_validation_script_passes() -> None:
    project_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(project_root / "scripts" / "validate_deployment.py")],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "Deployment scaffold validation passed." in result.stdout
