from __future__ import annotations

from typing import Protocol


class RateLimiter(Protocol):
    def hit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        """
        Returns: (allowed, remaining, reset_epoch_seconds)
        """
