import betfairlightweight
from betfairlightweight import filters
import pandas as pd
import numpy as np
import os
import datetime
import json

# Setting up credentials and certifications
certifications = os.path.join(os.getcwd(), 'certifications')

with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
  credentials = json.loads(f.read())

# Validating interaction with API
trading = betfairlightweight.APIClient(username=credentials['username'],
                                       password=credentials['password'],
                                       app_key=credentials['app_key'],
                                       certs=certifications)

trading.login()

# Return eventIDs for a sport
def event_id(sport):
  # Filter for a sport
  sport_filter = betfairlightweight.filters.market_filter(text_query=sport)
  sport_event_type = trading.betting.list_event_types(filter=sport_filter)
  sport_event_type = sport_event_type[0]
  sport_event_type_id = sport_event_type.event_type.id

  # Use sport to define a market filter 
  sport_event_filter = betfairlightweight.filters.market_filter(event_type_ids=[sport_event_type_id])

  # Get a list of all events as objects
  sport_events = trading.betting.list_events(filter=sport_event_filter)

  # Create a DataFrame with all the events for a sport
  current_markets_available = pd.DataFrame({
      'Event Name': [event_object.event.name for event_object in sport_events],
      'Event ID': [event_object.event.id for event_object in sport_events],
      'Market Count': [event_object.market_count for event_object in sport_events]
  })  
  print(current_markets_available)

# List markets for a given event ID
def list_markets_for_event(eventID):
  market_catalogue_filter = betfairlightweight.filters.market_filter(event_ids=[eventID])
  market_catalogues = trading.betting.list_market_catalogue(
    filter=market_catalogue_filter,
    max_results='100',
    sort='FIRST_TO_START'
  )
  #Put markets into dataframe
  market_types = pd.DataFrame({
    'Market Name': [market_cat_object.market_name for market_cat_object in market_catalogues],
    'Market ID': [market_cat_object.market_id for market_cat_object in market_catalogues],
    'Total Matched': [market_cat_object.total_matched for market_cat_object in market_catalogues],
  })
  print(market_types)

trading.logout()