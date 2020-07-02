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
                                                app_key=credentials['app_key'],
                                                certs=certifications)
    self.trading.login()


  def get_event_id(self, sport):
    ''' Returns the eventID for a sport '''
    sport_filter = betfairlightweight.filters.market_filter(text_query=sport)
    sport_event_type_id = self.trading.betting.list_event_types(filter=sport_filter)[0].event_type.id
    sport_event_filter = betfairlightweight.filters.market_filter(event_type_ids=[sport_event_type_id])
    sport_events = self.trading.betting.list_events(filter=sport_event_filter)

    current_markets_available_df = pd.DataFrame({
        'Event Name': [event_object.event.name for event_object in sport_events],
        'Event ID': [event_object.event.id for event_object in sport_events],
        'Market Count': [event_object.market_count for event_object in sport_events],
        'Datetime': [event_object.event.open_date for event_object in sport_events]
    })  
    current_markets_available_df['Datetime'] = pd.to_datetime(current_markets_available_df['Datetime'], format="%Y-%m-%d %H:%M:%S")
    return current_markets_available_df


  def get_event_markets(self, eventID):
    ''' List markets for a given event ID '''
    market_catalogue_filter = betfairlightweight.filters.market_filter(event_ids=[eventID])
    market_catalogues = self.trading.betting.list_market_catalogue( filter=market_catalogue_filter, max_results='100', sort='FIRST_TO_START')

    market_types_df = pd.DataFrame({
      'Market Name': [market_cat_object.market_name for market_cat_object in market_catalogues],
      'Market ID': [market_cat_object.market_id for market_cat_object in market_catalogues],
      'Total Matched': [market_cat_object.total_matched for market_cat_object in market_catalogues],
    })
    return market_types_df


  def get_runners_market_data(self, market_id, price_data):
    ''' Returns event filtered event data for all runners (last price traded and total matched) in a given market id
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
    market_book = self.trading.betting.list_market_book(market_ids=[market_id], price_projection=price_filter)[0]
    runners = market_book.runners
    selection_ids = [runner_book.selection_id for runner_book in runners]
    last_prices_traded = [runner_book.last_price_traded for runner_book in runners]
    total_matched = [runner_book.total_matched for runner_book in runners]

    runners_df = pd.DataFrame({
        'Selection ID': selection_ids,
        'Last Price Traded': last_prices_traded,
        'Total Matched': total_matched,
    })
    return runners_df


  def covert_price_to_probability(self, runners_df):
      ''' Returns probability for runners dataframe'''
      probability_dict = {}
      for row in range(runners_df.shape[0]):
        # In the future add functionality for driver/team name
        selection_id = runners_df.iloc[row]['Selection ID']
        last_price_traded = runners_df.iloc[row]['Last Price Traded']
        if last_price_traded is None:
          probability_dict[selection_id] = math.nan
        else:
          probability_dict[selection_id] = round(((1/last_price_traded) * 100), 2)
      return probability_dict 
    


'''
Get runner meta data

market_catalogue_filter = betfairlightweight.filters.market_filter(event_ids=[29570037])
f1_outrights = betfair.trading.betting.list_market_catalogue(filter=market_catalogue_filter, max_results=100)[1]
print(f1_outrights.runners)       # When premium this should return runners
'''