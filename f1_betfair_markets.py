class F1BetfairMarkets:
    def __init__(self, betfair, motorsport_events):
        self.betfair = betfair
        self.motorsport_events = motorsport_events

        self.outright_event_name = None
        self.outright_championship_markets = None

        self.next_race_event_name = None
        self.next_race_markets = None


    def get_outright_championship_markets(self):
        ''' Lazily returns tuple of event name and markets available for outright championship e.g WDC, WCC '''
        if self.outright_event_name is None and self.outright_championship_markets is None:
            for event in self.motorsport_events:
                if event.event.name.startswith('F1 Outrights'):
                    self.outright_event_name = event.event.name
                    self.outright_championship_markets = self.betfair.get_event_markets(event.event.id)
                    break
        return (self.outright_event_name, self.outright_championship_markets)


    def get_next_f1_race_markets(self, next_race_datetime):
        ''' Lazily returns tuple of event name and markets available for next race e.g fastest lap, race winner, pole position '''
        if self.next_race_event_name is None and self.next_race_markets is None:
            for event in self.motorsport_events:
                if event.event.open_date.date() == next_race_datetime.date():
                    self.next_race_event_name = event.event.name
                    self.next_race_markets = self.betfair.get_event_markets(event.event.id)
                    break
        return (self.next_race_event_name, self.next_race_markets)
        