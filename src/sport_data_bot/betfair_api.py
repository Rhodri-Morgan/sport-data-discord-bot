"""Thin wrapper around betfairlightweight for Discord-bot usage."""

from __future__ import annotations

import os

import betfairlightweight


class BetFairAPI:
    """Authenticated BetFair API client with helpers for events, markets, and probabilities."""

    def __init__(self, certifications: str) -> None:
        """Create and log in a BetFair trading client using env-var credentials."""
        self.trading = betfairlightweight.APIClient(
            username=os.environ["BETFAIR_USERNAME"],
            password=os.environ["BETFAIR_PASSWORD"],
            app_key=os.environ["BETFAIR_LIVE_APP_KEY"],
            certs=certifications,
        )
        self.trading.login()

    def get_event_types(self) -> list:
        """Return all event types hosted by BetFair."""
        return self.trading.betting.list_event_types()

    def get_events(self, sport: str) -> list:
        """Return event result objects for a given sport."""
        sport_filter = betfairlightweight.filters.market_filter(text_query=sport)
        sport_event_type_id = self.trading.betting.list_event_types(filter=sport_filter)[0].event_type.id
        sport_event_filter = betfairlightweight.filters.market_filter(event_type_ids=[sport_event_type_id])
        return self.trading.betting.list_events(filter=sport_event_filter)

    def get_event_markets(self, event_id: str) -> list:
        """Return market catalogues for a given event id."""
        market_catalogue_filter = betfairlightweight.filters.market_filter(event_ids=[event_id])
        return self.trading.betting.list_market_catalogue(filter=market_catalogue_filter, max_results=1000, sort="FIRST_TO_START")

    def get_market_book(self, market_id: str):
        """Return the market book object for a given market id."""
        return self.trading.betting.list_market_book(market_ids=[market_id])[0]

    def calculate_runners_probability(self, runners, runners_names: dict) -> dict:
        """Return a name → percent-probability dict sorted descending by probability."""
        probability_dict: dict = {}
        for runner in runners:
            name = runners_names[runner.selection_id]
            last_price_traded = runner.last_price_traded
            if last_price_traded is not None:
                probability_dict[name] = round(((1 / last_price_traded) * 100), 2)

        return {k: v for k, v in sorted(probability_dict.items(), key=lambda item: item[1], reverse=True)}

    def get_runners_names(self, market_id: str) -> dict:
        """Return a selection_id → runner_name dict for a given market id."""
        market_catalogue_filter = betfairlightweight.filters.market_filter(market_ids=[market_id])
        market_catalogue = self.trading.betting.list_market_catalogue(
            filter=market_catalogue_filter, max_results=1, market_projection=["RUNNER_DESCRIPTION", "RUNNER_METADATA"]
        )[0]
        runners_names: dict = {}
        for runner in market_catalogue.runners:
            if runner.runner_name:
                runners_names[runner.selection_id] = runner.runner_name.strip()
        return runners_names
