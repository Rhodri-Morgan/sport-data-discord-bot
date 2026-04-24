"""Shared pytest fixtures and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest


@pytest.fixture(autouse=True)
def _stub_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide dummy values for required env vars so ``config.from_env`` does not blow up."""
    for key in ("DISCORD_BOT_TOKEN", "BETFAIR_USERNAME", "BETFAIR_PASSWORD", "BETFAIR_LIVE_APP_KEY", "AWS_BUCKET_NAME"):
        monkeypatch.setenv(key, "dummy")


# ---------------------------------------------------------------------------
# Fake BetFair domain objects (matching the betfairlightweight surface area)
# ---------------------------------------------------------------------------


@dataclass
class FakeEvent:
    """Minimal stand-in for ``betfairlightweight.resources.bettingresources.Event``."""

    id: str
    name: str
    open_date: datetime | None


@dataclass
class FakeEventResult:
    """Minimal stand-in for an ``EventResult`` returned by ``list_events``."""

    event: FakeEvent
    market_count: int = 1


@dataclass
class FakeMarketCatalogue:
    """Minimal stand-in for a ``MarketCatalogue`` returned by ``list_market_catalogue``."""

    market_id: str
    market_name: str


@dataclass
class FakeRunner:
    """Minimal stand-in for a runner inside a market book."""

    selection_id: int
    last_price_traded: float | None


def make_event_result(
    name: str,
    *,
    event_id: str | None = None,
    open_date: datetime | None = None,
) -> FakeEventResult:
    """Build a fake EventResult-like object for tests."""
    return FakeEventResult(
        event=FakeEvent(
            id=event_id or f"evt-{name}",
            name=name,
            open_date=open_date,
        ),
    )


def make_market(name: str, *, market_id: str | None = None) -> FakeMarketCatalogue:
    """Build a fake market catalogue object for tests."""
    return FakeMarketCatalogue(market_id=market_id or f"mkt-{name}", market_name=name)


def utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """Convenience builder for tz-aware UTC datetimes."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


__all__ = [
    "FakeEvent",
    "FakeEventResult",
    "FakeMarketCatalogue",
    "FakeRunner",
    "make_event_result",
    "make_market",
    "utc",
]
