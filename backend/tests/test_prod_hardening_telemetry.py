from __future__ import annotations

from dataclasses import dataclass, field

from app.main import create_app
from fastapi.testclient import TestClient


@dataclass
class _FakeTelemetry:
    counters: list[tuple[str, int, dict[str, str]]] = field(default_factory=list)
    histograms: list[tuple[str, float, dict[str, str]]] = field(default_factory=list)

    def incr_counter(
        self, name: str, value: int = 1, tags: dict[str, str] | None = None
    ) -> None:
        self.counters.append((name, value, tags or {}))

    def observe_histogram(
        self, name: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        self.histograms.append((name, value, tags or {}))


def test_telemetry_middleware_calls_telemetry() -> None:
    app = create_app()
    fake = _FakeTelemetry()
    app.state.telemetry = fake

    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200

    assert any(name == "http_requests_total" for (name, _v, _t) in fake.counters)
    assert any(name == "http_request_duration_ms" for (name, _v, _t) in fake.histograms)
