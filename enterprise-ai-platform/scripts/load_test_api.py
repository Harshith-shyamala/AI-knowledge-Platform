from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class Measurement:
    name: str
    status_code: int
    latency_ms: float


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a lightweight EAKP API load test.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--email-prefix", default="loadtest")
    args = parser.parse_args()

    if args.iterations < 1:
        raise SystemExit("--iterations must be >= 1")

    with httpx.Client(base_url=args.base_url, timeout=30.0) as client:
        context = _bootstrap(client, args.email_prefix)
        measurements: list[Measurement] = []
        for index in range(args.iterations):
            measurements.extend(_run_iteration(client, context, index))

    print(json.dumps(_summary(measurements), indent=2))


def _bootstrap(client: httpx.Client, email_prefix: str) -> dict[str, str]:
    timestamp = int(time.time())
    session = _request_json(
        client,
        "POST",
        "/auth/register",
        json={
            "email": f"{email_prefix}-{timestamp}@example.com",
            "password": "correct horse battery staple",
            "display_name": "Load Test User",
            "organization_name": f"Load Test Org {timestamp}",
        },
    )
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    headers = {"Authorization": f"Bearer {token}"}
    workspace = _request_json(
        client,
        "POST",
        f"/organizations/{organization_id}/workspaces",
        headers=headers,
        json={"name": "Knowledge"},
    )
    workspace_id = workspace["id"]
    document = _request_json(
        client,
        "POST",
        f"/organizations/{organization_id}/workspaces/{workspace_id}/documents",
        headers=headers,
        data={"title": "Access Review Policy"},
        files={
            "file": (
                "policy.md",
                b"Quarterly access reviews require manager approval and audit evidence.",
                "text/markdown",
            )
        },
    )
    document_id = document["document"]["id"]
    _request_json(
        client,
        "POST",
        f"/organizations/{organization_id}/workspaces/{workspace_id}/documents/{document_id}/index",
        headers=headers,
    )
    return {
        "token": token,
        "organization_id": organization_id,
        "workspace_id": workspace_id,
    }


def _run_iteration(
    client: httpx.Client,
    context: dict[str, str],
    index: int,
) -> list[Measurement]:
    del index
    headers = {"Authorization": f"Bearer {context['token']}"}
    prefix = f"/organizations/{context['organization_id']}/workspaces/{context['workspace_id']}"
    return [
        _measure(
            client,
            "search",
            "POST",
            f"{prefix}/search",
            headers=headers,
            json={"query": "manager approval audit evidence", "top_k": 5},
        ),
        _measure(
            client,
            "chat",
            "POST",
            f"{prefix}/chat",
            headers=headers,
            json={"message": "What do quarterly access reviews require?", "top_k": 5},
        ),
        _measure(
            client,
            "agent",
            "POST",
            f"{prefix}/agents/runs",
            headers=headers,
            json={"question": "What do quarterly access reviews require?", "top_k": 5},
        ),
        _measure(
            client,
            "evaluation",
            "POST",
            f"{prefix}/evaluation/runs",
            headers=headers,
            json={
                "examples": [
                    {
                        "question": "What do quarterly access reviews require?",
                        "expected_answer": "manager approval and audit evidence",
                    }
                ],
                "top_k": 5,
            },
        ),
    ]


def _measure(
    client: httpx.Client,
    name: str,
    method: str,
    path: str,
    **kwargs: Any,
) -> Measurement:
    started_at = time.perf_counter()
    response = client.request(method, path, **kwargs)
    latency_ms = round((time.perf_counter() - started_at) * 1000, 3)
    response.raise_for_status()
    return Measurement(name=name, status_code=response.status_code, latency_ms=latency_ms)


def _request_json(client: httpx.Client, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    response = client.request(method, path, **kwargs)
    response.raise_for_status()
    return dict(response.json())


def _summary(measurements: list[Measurement]) -> dict[str, Any]:
    grouped: dict[str, list[Measurement]] = {}
    for measurement in measurements:
        grouped.setdefault(measurement.name, []).append(measurement)

    return {
        name: {
            "count": len(items),
            "status_codes": sorted({item.status_code for item in items}),
            "p50_ms": _percentile([item.latency_ms for item in items], 0.50),
            "p95_ms": _percentile([item.latency_ms for item in items], 0.95),
            "max_ms": max(item.latency_ms for item in items),
        }
        for name, items in sorted(grouped.items())
    }


def _percentile(values: list[float], percentile: float) -> float:
    if len(values) == 1:
        return values[0]
    return round(statistics.quantiles(values, n=100)[max(0, int(percentile * 100) - 1)], 3)


if __name__ == "__main__":
    main()
