class F1BetfairMarkets:
    def __init__(self, betfair, motorsport_events):
        self.betfair = betfair
        self.motorsport_events = motorsport_events
        self.f1_outright_championship_markets = None


    def get_f1_outright_championship_markets(self):
        ''' Lazily gets F1 markets for outright championship e.g WDC, WCC '''
        if self.f1_outright_championship_markets is None:
            f1_outright = self.motorsport_events.loc[self.motorsport_events['Event Name'] == 'F1 Outrights 2020']
            f1_outright_event_id = f1_outright.iloc[0]['Event ID']
            self.f1_outright_championship_markets = self.betfair.get_event_markets(f1_outright_event_id)
        return self.f1_outright_championship_markets