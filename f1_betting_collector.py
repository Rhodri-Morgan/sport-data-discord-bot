import betfair_api
import f1_betfair_markets
import f1_meta_collector
import datetime
import pandas as pd


class F1BettingCollector:
    def __init__(self): 
        self.betfair = betfair_api.BetFairAPI()
        self.motorsport_events = self.betfair.get_event_id('Motor Sport')
        self.f1_meta = f1_meta_collector.F1MetaCollector()
        self.f1_markets = f1_betfair_markets.F1BetfairMarkets(self.betfair, self.motorsport_events)
        self.price_data = 'EX_BEST_OFFERS'            


    def get_championship_outright_winner_probabilities(self):
        ''' Gets the outright championship probabilities for all markets, returns dict with market name as key and proabilities as values '''
        outright_dict = {}
        outright_markets = self.f1_markets.get_f1_outright_championship_markets()
        for row in range(outright_markets.shape[0]):
            outright_market_id = outright_markets.iloc[row]['Market ID']
            outright_market_name = outright_markets.iloc[row]['Market Name']
            outright_runners = self.betfair.get_runners_market_data(outright_market_id, self.price_data)
            print(outright_runners)
            outright_probabilities = self.betfair.covert_price_to_probability(outright_runners)
            outright_dict[outright_market_name] = outright_probabilities
        return outright_dict
    

    def get_next_race_probabilities(self):
        ''' Gets the next race probabilities for all markets, returns dict with market name as key and proabilities as values '''
        next_race_dict = {}
        next_race_datetime = self.f1_meta.get_race_datetime(self.f1_meta.get_next_race())
        next_race_markets = self.f1_markets.get_next_f1_race_markets(next_race_datetime)
        for row in range(next_race_markets.shape[0]):
            next_race_market_id = next_race_markets.iloc[row]['Market ID']
            next_race_market_name = next_race_markets.iloc[row]['Market Name']
            next_race_runners = self.betfair.get_runners_market_data(next_race_market_id, self.price_data)
            next_race_probabilities = self.betfair.covert_price_to_probability(next_race_runners)
            next_race_dict[next_race_market_name] = next_race_probabilities
        return next_race_dict


f1_betfair_collector = F1BettingCollector()
f1_betfair_collector.get_championship_outright_winner_probabilities()