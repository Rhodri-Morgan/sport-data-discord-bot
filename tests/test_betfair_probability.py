"""Tests for the BetFair probability calculation logic."""

from __future__ import annotations

from unittest.mock import patch

from sport_data_bot.betfair_api import BetFairAPI
from tests.conftest import FakeRunner


def _make_api() -> BetFairAPI:
    """Construct a BetFairAPI without triggering its real ``login()`` call."""
    with patch("sport_data_bot.betfair_api.betfairlightweight.APIClient") as client_cls:
        client_cls.return_value.login.return_value = None
        return BetFairAPI(certifications="/tmp/certs")


def test_probability_inverts_decimal_odds_to_percent():
    api = _make_api()
    runners = [
        FakeRunner(selection_id=1, last_price_traded=2.0),
        FakeRunner(selection_id=2, last_price_traded=4.0),
    ]
    names = {1: "Alpha", 2: "Bravo"}
    result = api.calculate_runners_probability(runners, names)

    # 1/2.0 → 50%, 1/4.0 → 25%
    assert result == {"Alpha": 50.0, "Bravo": 25.0}


def test_probability_skips_runners_without_last_price():
    api = _make_api()
    runners = [
        FakeRunner(selection_id=1, last_price_traded=2.0),
        FakeRunner(selection_id=2, last_price_traded=None),
    ]
    names = {1: "Alpha", 2: "Bravo"}
    result = api.calculate_runners_probability(runners, names)

    assert "Bravo" not in result
    assert result == {"Alpha": 50.0}


def test_probability_sorted_descending():
    api = _make_api()
    runners = [
        FakeRunner(selection_id=1, last_price_traded=10.0),  # 10%
        FakeRunner(selection_id=2, last_price_traded=2.0),  # 50%
        FakeRunner(selection_id=3, last_price_traded=4.0),  # 25%
    ]
    names = {1: "C", 2: "A", 3: "B"}
    result = api.calculate_runners_probability(runners, names)

    assert list(result.keys()) == ["A", "B", "C"]
    assert list(result.values()) == [50.0, 25.0, 10.0]


def test_probability_rounds_to_two_decimals():
    api = _make_api()
    runners = [FakeRunner(selection_id=1, last_price_traded=3.0)]  # 33.333...%
    result = api.calculate_runners_probability(runners, runners_names={1: "Alpha"})
    assert result == {"Alpha": 33.33}


def test_probability_market_efficiency_sums_close_to_100_for_two_horse():
    api = _make_api()
    runners = [
        FakeRunner(selection_id=1, last_price_traded=2.0),  # 50%
        FakeRunner(selection_id=2, last_price_traded=2.0),  # 50%
    ]
    names = {1: "Alpha", 2: "Bravo"}
    result = api.calculate_runners_probability(runners, names)
    assert sum(result.values()) == 100.0


def test_probability_empty_runners_returns_empty_dict():
    api = _make_api()
    assert api.calculate_runners_probability([], runners_names={}) == {}
