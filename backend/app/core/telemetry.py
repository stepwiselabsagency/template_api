from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from app.core.config import Settings

log = logging.getLogger("app.telemetry")


class Telemetry(Protocol):
    def incr_counter(
        self, name: str, value: int = 1, tags: dict[str, str] | None = None
    ) -> None: ...

    def observe_histogram(
        self, name: str, value: float, tags: dict[str, str] | None = None
    ) -> None: ...


@dataclass(frozen=True)
class NoopTelemetry:
    def incr_counter(
        self, name: str, value: int = 1, tags: dict[str, str] | None = None
    ) -> None:
        return None

    def observe_histogram(
        self, name: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        return None


@dataclass(frozen=True)
class LoggingTelemetry:
    """
    Template-friendly default "hook": emits metrics as structured logs.
    """

    def incr_counter(
        self, name: str, value: int = 1, tags: dict[str, str] | None = None
    ) -> None:
        log.info(
            "metric.counter",
            extra={"metric": name, "value": value, "tags": tags or {}},
        )

    def observe_histogram(
        self, name: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        log.info(
            "metric.histogram",
            extra={"metric": name, "value": value, "tags": tags or {}},
        )


def build_telemetry(settings: Settings) -> Telemetry:
    mode = (settings.TELEMETRY_MODE or "noop").strip().lower()
    if mode == "log":
        return LoggingTelemetry()
    return NoopTelemetry()
