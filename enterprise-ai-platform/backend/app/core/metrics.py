from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class RouteMetric:
    method: str
    path: str
    status_code: int
    count: int = 0
    total_latency_ms: float = 0.0
    max_latency_ms: float = 0.0


@dataclass
class MetricsRegistry:
    _routes: dict[tuple[str, str, int], RouteMetric] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        latency_ms: float,
    ) -> None:
        key = (method.upper(), path, status_code)
        with self._lock:
            metric = self._routes.get(key)
            if metric is None:
                metric = RouteMetric(method=key[0], path=key[1], status_code=key[2])
                self._routes[key] = metric
            metric.count += 1
            metric.total_latency_ms = round(metric.total_latency_ms + latency_ms, 6)
            metric.max_latency_ms = max(metric.max_latency_ms, latency_ms)

    def render_prometheus(self) -> str:
        with self._lock:
            metrics = sorted(
                self._routes.values(),
                key=lambda item: (item.path, item.method, item.status_code),
            )

        lines = [
            "# HELP eakp_http_requests_total Total HTTP requests by route.",
            "# TYPE eakp_http_requests_total counter",
        ]
        for metric in metrics:
            labels = _labels(metric.method, metric.path, metric.status_code)
            lines.append(f"eakp_http_requests_total{{{labels}}} {metric.count}")

        lines.extend(
            [
                "# HELP eakp_http_request_latency_ms_sum Total HTTP latency in milliseconds.",
                "# TYPE eakp_http_request_latency_ms_sum counter",
            ]
        )
        for metric in metrics:
            labels = _labels(metric.method, metric.path, metric.status_code)
            lines.append(
                f"eakp_http_request_latency_ms_sum{{{labels}}} "
                f"{metric.total_latency_ms:.6f}"
            )

        lines.extend(
            [
                "# HELP eakp_http_request_latency_ms_max Max HTTP latency in milliseconds.",
                "# TYPE eakp_http_request_latency_ms_max gauge",
            ]
        )
        for metric in metrics:
            labels = _labels(metric.method, metric.path, metric.status_code)
            lines.append(
                f"eakp_http_request_latency_ms_max{{{labels}}} "
                f"{metric.max_latency_ms:.6f}"
            )

        lines.append("")
        return "\n".join(lines)


def _labels(method: str, path: str, status_code: int) -> str:
    return (
        f'method="{_escape(method)}",'
        f'path="{_escape(path)}",'
        f'status_code="{status_code}"'
    )


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
