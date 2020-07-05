import http.client
import json
import os
from datetime import datetime


class F1MetaCollector:
    def __init__(self):
        with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
            self.credentials = json.loads(f.read())['sportradar']

        self.connection = http.client.HTTPSConnection("api.sportradar.us")
        self.races_data = self.request_races_data()


    def request_races_data(self):
        ''' Requests data from the sportradar API about races for F1 '''
        self.connection.request("GET", "/formula1/trial/v2/en/sport_events/sr:stage:547803/summary.json?api_key=" + self.credentials['api_key'])
        response = self.connection.getresponse()
        return json.loads(response.read())['stage']


    def request_race_data(self, id):
        ''' Requests data from the sportradar API about F1 race '''
        self.connection.request("GET", "/formula1/trial/v2/en/sport_events/" + id +"/summary.json?api_key=" + self.credentials['api_key'])
        response = self.connection.getresponse()
        race_data = json.loads(response.read())
        return race_data


    def get_race_end_datetime(self, race):
        ''' Returns datetime object of race ending datetime '''
        return datetime.strptime(str(race['scheduled_end'][0:10]+" "+race['scheduled_end'][11:19]).strip(), "%Y-%m-%d %H:%M:%S") 


    def get_race_end_date(self, race):
        ''' Returns datetime object of race ending date '''
        return datetime.strptime(str(race['scheduled_end'][0:10]), "%Y-%m-%d") 


    def get_next_race(self):
        ''' Returns JSON data for the next (soonest) F1 race '''
        soonest_race = None
        for race in self.races_data['stages']:
            race_datetime = self.get_race_end_datetime(race)
            current_datetime = datetime.utcnow()

            if soonest_race is None and race_datetime > current_datetime:
                soonest_race = race
            elif race_datetime > current_datetime and race_datetime < self.get_race_end_datetime(soonest_race):
                soonest_race = race
        return soonest_race
