"""Tests for the interactive sport → event → market views."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import discord
import pytest

from sport_data_bot.views import (
    PAGE_SIZE,
    EventSelectView,
    MarketSelectView,
    SportSelectView,
    _event_open_date,
    _format_event_label,
    _OwnedView,
)
from tests.conftest import make_event_result, make_market, utc

# ---------------------------------------------------------------------------
# Pure formatting helpers
# ---------------------------------------------------------------------------


def test_format_event_label_includes_open_date():
    event_result = make_event_result("Australian Grand Prix", open_date=utc(2026, 5, 12, 14, 30))
    assert _format_event_label(event_result) == "12 May 14:30 — Australian Grand Prix"


def test_format_event_label_falls_back_to_name_only():
    event_result = make_event_result("Grand National", open_date=None)
    assert _format_event_label(event_result) == "Grand National"


def test_format_event_label_truncates_to_100_chars():
    long_name = "A" * 200
    event_result = make_event_result(long_name, open_date=utc(2026, 5, 12, 14, 30))
    label = _format_event_label(event_result)
    assert len(label) == 100
    # Date prefix should still be present
    assert label.startswith("12 May 14:30 — ")


def test_format_event_label_strips_whitespace():
    event_result = make_event_result("  Spaced Name  ", open_date=None)
    assert _format_event_label(event_result) == "Spaced Name"


def test_event_open_date_returns_aware_datetime_unchanged():
    event_result = make_event_result("Race", open_date=utc(2026, 5, 1, 12, 0))
    assert _event_open_date(event_result) == utc(2026, 5, 1, 12, 0)


def test_event_open_date_attaches_utc_to_naive_datetime():
    naive = datetime(2026, 5, 1, 12, 0)
    event_result = make_event_result("Race", open_date=naive)
    out = _event_open_date(event_result)
    assert out.tzinfo == timezone.utc
    assert out.replace(tzinfo=None) == naive


def test_event_open_date_falls_back_to_far_future_when_missing():
    """Events without open_date sort to the end so they don't disrupt date-ordered lists."""
    event_result = make_event_result("Mystery Match", open_date=None)
    assert _event_open_date(event_result) == datetime.max.replace(tzinfo=timezone.utc)


def test_event_open_date_used_for_sorted_ordering():
    earlier = make_event_result("Earlier", open_date=utc(2026, 1, 1))
    later = make_event_result("Later", open_date=utc(2026, 6, 1))
    no_date = make_event_result("No Date", open_date=None)

    ordered = sorted([later, earlier, no_date], key=_event_open_date)
    assert [e.event.name for e in ordered] == ["Earlier", "Later", "No Date"]


# ---------------------------------------------------------------------------
# Owner-restricted view base
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_owned_view_allows_owner():
    view = _OwnedView(owner_id=42)
    interaction = MagicMock()
    interaction.user.id = 42
    assert await view.interaction_check(interaction) is True


@pytest.mark.asyncio
async def test_owned_view_blocks_non_owner():
    view = _OwnedView(owner_id=42)
    interaction = MagicMock()
    interaction.user.id = 99
    interaction.response.send_message = MagicMock(return_value=_async_noop())
    assert await view.interaction_check(interaction) is False
    interaction.response.send_message.assert_called_once()
    args, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("ephemeral") is True


# ---------------------------------------------------------------------------
# SportSelectView — single page of sports
# ---------------------------------------------------------------------------


def _fake_sport(name: str) -> MagicMock:
    sport = MagicMock()
    sport.event_type.name = name
    return sport


def test_sport_select_view_creates_one_select_with_options():
    sports = [_fake_sport(n) for n in ("Motor Sport", "Rugby Union", "Soccer")]
    view = SportSelectView(bot=MagicMock(), owner_id=1, sports=sports)

    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 1
    options = selects[0].options
    assert [o.value for o in options] == ["Motor Sport", "Rugby Union", "Soccer"]
    assert [o.label for o in options] == ["Motor Sport", "Rugby Union", "Soccer"]


def test_sport_select_view_caps_options_to_page_size():
    sports = [_fake_sport(f"Sport {i}") for i in range(40)]
    view = SportSelectView(bot=MagicMock(), owner_id=1, sports=sports)

    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects[0].options) == PAGE_SIZE


# ---------------------------------------------------------------------------
# EventSelectView — pagination behaviour
# ---------------------------------------------------------------------------


def _build_events(n: int) -> list:
    return [make_event_result(f"Event {i:03d}", open_date=utc(2026, 5, 1, 12, i % 60)) for i in range(n)]


def test_event_select_single_page_hides_no_options_required():
    events = _build_events(5)
    view = EventSelectView(bot=MagicMock(), owner_id=1, sport="Football", events=events)

    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 1
    assert len(selects[0].options) == 5
    assert view.total_pages == 1

    prev = next(b for b in buttons if b.label == "← Previous")
    nxt = next(b for b in buttons if b.label == "Next →")
    page_indicator = next(b for b in buttons if b.label.startswith("Page "))
    assert prev.disabled is True
    assert nxt.disabled is True
    assert page_indicator.label == "Page 1/1"


def test_event_select_paginates_when_over_25_events():
    events = _build_events(60)
    view = EventSelectView(bot=MagicMock(), owner_id=1, sport="Football", events=events)
    assert view.total_pages == 3

    # Page 1: 25 events, prev disabled, next enabled
    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    assert len(select.options) == PAGE_SIZE
    prev = next(c for c in view.children if isinstance(c, discord.ui.Button) and c.label == "← Previous")
    nxt = next(c for c in view.children if isinstance(c, discord.ui.Button) and c.label == "Next →")
    assert prev.disabled is True
    assert nxt.disabled is False


def test_event_select_last_page_disables_next():
    events = _build_events(60)
    view = EventSelectView(bot=MagicMock(), owner_id=1, sport="Football", events=events, page=2)

    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    # Last page should have 60 - 50 = 10 events
    assert len(select.options) == 10
    nxt = next(c for c in view.children if isinstance(c, discord.ui.Button) and c.label == "Next →")
    prev = next(c for c in view.children if isinstance(c, discord.ui.Button) and c.label == "← Previous")
    assert nxt.disabled is True
    assert prev.disabled is False


def test_event_select_option_value_is_global_event_index():
    """Select values must be absolute indices into the events list, not page-local."""
    events = _build_events(40)
    view = EventSelectView(bot=MagicMock(), owner_id=1, sport="Football", events=events, page=1)
    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    values = [int(o.value) for o in select.options]
    assert values == list(range(25, 40))


# ---------------------------------------------------------------------------
# MarketSelectView — pagination behaviour (markets typically <25 but pagination supported)
# ---------------------------------------------------------------------------


def test_market_select_single_page_hides_pagination_buttons():
    markets = [make_market(f"M{i}") for i in range(10)]
    view = MarketSelectView(bot=MagicMock(), owner_id=1, sport="Football", event_result=make_event_result("Final"), markets=markets)

    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 1
    assert len(buttons) == 0  # no pagination needed


def test_market_select_shows_pagination_when_over_25():
    markets = [make_market(f"M{i:02d}") for i in range(30)]
    view = MarketSelectView(bot=MagicMock(), owner_id=1, sport="Football", event_result=make_event_result("Final"), markets=markets)
    assert view.total_pages == 2

    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    labels = {b.label for b in buttons}
    assert "← Previous" in labels
    assert "Next →" in labels


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _async_noop():
    return None
