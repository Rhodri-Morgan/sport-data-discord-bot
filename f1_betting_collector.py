import betfair_api
import f1_betfair_markets
import f1_meta_collector


class F1BettingCollector:
    def __init__(self): 
        self.betfair = betfair_api.BetFairAPI()
        self.motorsport_events = self.betfair.get_events('Motor Sport')
        self.f1_meta = f1_meta_collector.F1MetaCollector()
        self.f1_markets = f1_betfair_markets.F1BetfairMarkets(self.betfair, self.motorsport_events)
        self.price_data = 'EX_BEST_OFFERS'            


    def get_championship_outright_winner_str(self):
        ''' Returns tuple of outright_winner event name and outright_winner string representation of available markets (returns None if not open) '''
        outright_name, outright_markets = self.f1_markets.get_outright_championship_markets()
        if outright_name is None and outright_markets is None:
            outright_str = None
        else:
            outright_str = ''
            for outright_market in outright_markets:
                outright_str = outright_str + outright_market.market_name + ' ' + '\n'
        return (outright_name, outright_str)


    def get_championship_outright_winner_probabilities(self):
        ''' Returns outright championship markets dictionary of key=market_name and value=probability_dict '''
        outright_dict = {}
        for outright_market in self.f1_markets.get_outright_championship_markets()[1]:
            outright_market_book = self.betfair.get_market_book(outright_market.market_id, self.price_data)
            outright_runners_names = self.betfair.get_runners_names(outright_market.market_id)
            outright_dict[outright_market.market_name] = self.betfair.calculate_runners_probability(outright_market_book.runners, outright_runners_names)
        return outright_dict
    

    def get_next_race_str(self):
        ''' Returns tuple of next_race event name and next_race string representation of available markets (returns None if not open) '''
        next_race_datetime = self.f1_meta.get_race_end_datetime(self.f1_meta.get_next_race())
        next_race_name, next_race_markets = self.f1_markets.get_next_f1_race_markets(next_race_datetime)
        if next_race_name is None and next_race_markets is None:
            next_race_str = None
        else:
            next_race_str = ''
            for next_race_market in next_race_markets:
                next_race_str = next_race_str + next_race_market.market_name + '\n'
        return (next_race_name, next_race_str)
    

    def get_next_race_probabilities(self):
        ''' Returns next race markets dictionary of key=market_name and value=probability_dict '''
        next_race_dict = {}
        next_race_datetime = self.f1_meta.get_race_end_datetime(self.f1_meta.get_next_race())
        for next_race_market in self.f1_markets.get_next_f1_race_markets(next_race_datetime)[1]:
            next_race_market_book = self.betfair.get_market_book(next_race_market.market_id, self.price_data)
            next_race_runners_names = self.betfair.get_runners_names(next_race_market.market_id)
            next_race_dict[next_race_market.market_name] = self.betfair.calculate_runners_probability(next_race_market_book.runners, next_race_runners_names)
        return next_race_dict
