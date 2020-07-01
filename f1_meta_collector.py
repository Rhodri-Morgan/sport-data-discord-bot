import http.client
import json
import os
import datetime


connection = http.client.HTTPSConnection("api.sportradar.us")
certifications = os.path.join(os.getcwd(), 'certifications')
with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
    credentials = json.loads(f.read())['sportradar']


def request_races_data():
    ''' Requests data from the sportradar API about races for F1 '''
    connection.request("GET", "/formula1/trial/v2/en/sport_events/sr:stage:547803/summary.json?api_key=" + credentials['api_key'])
    response = connection.getresponse()
    race_data = json.loads(response.read())
    return race_data['stage']


def get_race_datetime(race):
    ''' Extracts time and date from race and creates a datetime object '''
    race_string = str(race['scheduled'][0:10]+" "+race['scheduled'][11:19]).strip()    
    return datetime.datetime.strptime(race_string, "%Y-%m-%d %H:%M:%S") 


def find_next_race(races_data):
    ''' Finds the next (soonest) race for F1 and returns relevent index '''
    soonest_race = None
    for race in races_data['stages']:
        race_datetime = get_race_datetime(race)
        current_datetime = datetime.datetime.utcnow()
        if soonest_race is None and race_datetime > current_datetime:
            soonest_race = race
        elif race_datetime > current_datetime and race_datetime < get_race_datetime(soonest_race):
            soonest_race = race
    return soonest_race



race_data = request_races_data()
print(find_next_race(race_data))        # Grosser Preis von Osterreich 2020