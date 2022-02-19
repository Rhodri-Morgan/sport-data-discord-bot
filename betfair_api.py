import json
import math
import os

import betfairlightweight
from betfairlightweight import filters


class BetFairAPI:
    def __init__(self, certifications):
        self.trading = betfairlightweight.APIClient(username=os.environ.get('BETFAIR_USERNAME'),
                                                    password=os.environ.get('BETFAIR_PASSWORD'),
                                                    app_key=os.environ.get('BETFAIR_LIVE_APP_KEY'),
                                                    certs=certifications)
        self.trading.login()


    def get_event_types(self):
        """ Returns event types hosted by BetFair """
        return self.trading.betting.list_event_types()


    def get_events(self, sport):
        """ Returns event_result objects for a sport  """
        sport_filter = betfairlightweight.filters.market_filter(text_query=sport)
        sport_event_type_id = self.trading.betting.list_event_types(filter=sport_filter)[0].event_type.id
        sport_event_filter = betfairlightweight.filters.market_filter(event_type_ids=[sport_event_type_id])
        return self.trading.betting.list_events(filter=sport_event_filter)


    def get_event_markets(self, event_id):
        """ Returns list of market_catalogues for a given event id """
        market_catalogue_filter = betfairlightweight.filters.market_filter(event_ids=[event_id])
        return self.trading.betting.list_market_catalogue(filter=market_catalogue_filter,
                                                          max_results='1000',
                                                          sort='FIRST_TO_START')


    def get_market_book(self, market_id):
        """ Returns market_book object for a given event_id """
        return self.trading.betting.list_market_book(market_ids=[market_id])[0]


    def calculate_runners_probability(self, runners, runners_names):
        """ Returns dictionary of key=runner_name and value=probability for runners in a market_book """
        probability_dict = {}
        for runner in runners:
            name = runners_names[runner.selection_id]
            last_price_traded = runner.last_price_traded

            if last_price_traded is not None:
                probability_dict[name] = round(((1/last_price_traded) * 100), 2)

        return {k: v for k, v in sorted(probability_dict.items(), key=lambda item: item[1], reverse=True)}


    def get_runners_names(self, market_id):
        """ Returns dictionary of key=selection_id and value=runner_name for a given market_id """
        market_catalogue_filter = betfairlightweight.filters.market_filter(market_ids=[market_id])
        market_catalogue = self.trading.betting.list_market_catalogue(filter=market_catalogue_filter,
                                                                      max_results=1,
                                                                      market_projection=['RUNNER_DESCRIPTION', 'RUNNER_METADATA'])[0]
        runners_names = {}
        for runner in market_catalogue.runners:
            runners_names[runner.selection_id] = runner.runner_name.strip()
        return runners_names
