import betfairlightweight
from betfairlightweight import filters
import pandas as pd
import numpy as np
import math
import os
import datetime
import json


class BetFairAPI:
  def __init__(self):
    certifications = os.path.join(os.getcwd(), 'certifications')

    with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
      credentials = json.loads(f.read())['betfair']

    self.trading = betfairlightweight.APIClient(username=credentials['username'],
                                                password=credentials['password'],
                                                app_key=credentials['delayed_app_key'],
                                                certs=certifications)
    self.trading.login()


  def get_events(self, sport):
    ''' Returns event_result objects for a sport 
        param sport:
          Motor Sport - Formula 1 and other driving/racing based sports.
    '''
    if sport not in ['Motor Sport']:
      raise Exception('Invalid sport for get_events() check function comments.')

    sport_filter = betfairlightweight.filters.market_filter(text_query=sport)
    sport_event_type_id = self.trading.betting.list_event_types(filter=sport_filter)[0].event_type.id
    sport_event_filter = betfairlightweight.filters.market_filter(event_type_ids=[sport_event_type_id])
    return self.trading.betting.list_events(filter=sport_event_filter)


  def get_event_markets(self, eventID):
    ''' Returns list of market_catalogues for a given event id '''
    market_catalogue_filter = betfairlightweight.filters.market_filter(event_ids=[eventID])
    return self.trading.betting.list_market_catalogue(filter=market_catalogue_filter, 
                                                      max_results='1000', 
                                                      sort='FIRST_TO_START')


  def get_market_book(self, market_id, price_data):
    ''' Returns market_book object for a given event_id with a price_data filter applied 
        param price_data: 
          SP_AVAILABLE - Amount available for the BSP auction.
          SP_TRADED - Amount traded in the BSP auction.
          EX_BEST_OFFERS - Only the best prices available for each runner, to requested price depth.
          EX_ALL_OFFERS - EX_ALL_OFFERS trumps EX_BEST_OFFERS if both settings are present
          EX_TRADED - Amount traded on the exchange.
    '''
    if price_data not in ['SP_AVAILABLE', 'SP_TRADED', 'EX_BEST_OFFERS', 'EX_ALL_OFFERS', 'EX_TRADED']:
      raise Exception('Invalid price_data for get_runners_market_data() check function comments.')
    
    price_filter = betfairlightweight.filters.price_projection(price_data=[price_data])
    return self.trading.betting.list_market_book(market_ids=[market_id], price_projection=price_filter)[0]


  def calculate_runners_probability(self, runners, runners_names):
    ''' Returns dictionary of key=runner_name and value=probability for runners in a market_book'''
    probability_dict = {}
    for runner in runners:
      name = runners_names[runner.selection_id]
      last_price_traded = runner.last_price_traded

      if last_price_traded is None:
        probability_dict[name] = math.nan
      else:
        probability_dict[name] = round(((1/last_price_traded) * 100), 2)

    return probability_dict 
    
  
  def get_runners_names(self, market_id):
    ''' Returns dictionary of key=selection_id and value=runner_name for a given market_id '''
    market_catalogue_filter = betfairlightweight.filters.market_filter(market_ids=[market_id])
    market_catalogue = self.trading.betting.list_market_catalogue(filter=market_catalogue_filter, 
                                                                  max_results=1, 
                                                                  market_projection=["RUNNER_DESCRIPTION", "RUNNER_METADATA"])[0]
    runners_names = {}
    for runner in market_catalogue.runners:
      runners_names[runner.selection_id] = runner.runner_name.strip()
    return runners_names