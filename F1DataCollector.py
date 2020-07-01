import BetFairAPI
import F1BetfairMarkets


betfair = BetFairAPI.BetFairAPI()
motorsport_events = betfair.get_event_id('Motor Sport')
f1_markets = F1BetfairMarkets.F1BetfairMarkets(betfair, motorsport_events)
price_data = 'EX_BEST_OFFERS'            


def get_championship_outright_winner_probabilities(market_name):
    ''' Gets the probabilities for outright winner of either the drivers or constructors championship
        param market_name: 
            'Winner - Drivers Championship' - Final winner of the F1 driver championship for the year.
            'Winner - Constructors Championship' - Final winner of the F1 constructors championship for the year.
    '''
    if market_name not in ['Winner - Drivers Championship', 'Winner - Constructors Championship']:
        raise Exception('Invalid market_name for get_championship_outright_winner_probabilities() check function comments.')
    
    f1_outright_markets = f1_markets.get_f1_outright_championship_markets()
    f1_outright_market = f1_outright_markets.loc[f1_outright_markets['Market Name'] == market_name]
    f1_outright_market_id = f1_outright_market.iloc[0]['Market ID']
    f1_outright_runners = betfair.get_runners_market_data(f1_outright_market_id, price_data)
    return betfair.price_to_probability_list(f1_outright_runners)

                                     
print(get_championship_outright_winner_probabilities('Winner - Drivers Championship'))
print(get_championship_outright_winner_probabilities('Winner - Constructors Championship'))