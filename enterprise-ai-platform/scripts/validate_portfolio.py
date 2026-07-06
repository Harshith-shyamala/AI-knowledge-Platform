from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/portfolio/case-study.md",
    "docs/portfolio/demo-script.md",
    "docs/portfolio/interview-guide.md",
    "docs/security/security-review.md",
    "docs/operations/performance-plan.md",
    "scripts/load_test_api.py",
]


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit(f"Missing portfolio files: {', '.join(missing)}")

    case_study = _read("docs/portfolio/case-study.md")
    _require("## Architecture", case_study, "case study architecture section")
    _require("## What I Built", case_study, "case study implementation section")
    _require("## Results", case_study, "case study results section")

    security = _read("docs/security/security-review.md")
    for phrase in [
        "Tenant Isolation",
        "Prompt Injection",
        "Upload Security",
        "Secrets",
        "Residual Risks",
    ]:
        _require(phrase, security, f"security review includes {phrase}")

    demo = _read("docs/portfolio/demo-script.md")
    for phrase in ["Upload", "Index", "Search", "Chat", "Agent", "Evaluation", "Metrics"]:
        _require(phrase, demo, f"demo script includes {phrase}")

    load_test = _read("scripts/load_test_api.py")
    _require("def _run_iteration", load_test, "load test has iteration runner")
    _require("p95_ms", load_test, "load test reports p95")

    print("Portfolio validation passed.")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _require(needle: str, haystack: str, label: str) -> None:
    if needle not in haystack:
        raise SystemExit(f"Portfolio validation failed: {label}")


if __name__ == "__main__":
    main()
