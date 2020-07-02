from num2words import num2words
import datetime
import os
import json
import math


class F1DataProcessor:
    def __init__(self): 
        self.world_drivers_champion_json = os.path.join(os.getcwd(), 'historic_data/world_drivers_champion.json')
        self.world_constructors_champion_json = os.path.join(os.getcwd(), 'historic_data/world_constructors_champion.json')


    def save_world_drivers_champion_data(self, world_drivers_champion_probabilities):
        ''' Saves world drivers champion probability data to JSON file in historic_data directory '''
        if not os.path.exists(self.world_drivers_champion_json):
            with open(self.world_drivers_champion_json, 'w') as f:
                json.dump(world_drivers_champion_probabilities, f)
        else:
            with open(self.world_drivers_champion_json) as f:
                world_drivers_champion_data = json.load(f)
            world_drivers_champion_merged = {**world_drivers_champion_data, **world_drivers_champion_probabilities}
            with open(self.world_drivers_champion_json, "w") as f:
                json.dump(world_drivers_champion_merged, f)


    def save_world_constructors_champion_data(self, world_constructors_champion_probabilities):
        ''' Saves world constructors champion probability data to JSON file in historic_data directory '''
        if not os.path.exists(self.world_constructors_champion_json):
            with open(self.world_constructors_champion_json, 'w') as f:
                json.dump(world_constructors_champion_probabilities, f)
        else:
            with open(self.world_constructors_champion_json) as f:
                world_constructors_champion_data = json.load(f)
            world_constructors_champion_merged = {**world_constructors_champion_data, **world_constructors_champion_probabilities}
            with open(self.world_constructors_champion_json, "w") as f:
                json.dump(world_constructors_champion_merged, f)


    def construct_daily_drivers_str(self, wdc_probabilities):
        yesterday_datetime = (datetime.datetime.utcnow() - datetime.timedelta(1)).strftime("%Y-%m-%d")
        if os.path.exists(self.world_constructors_champion_json):
            with open(self.world_drivers_champion_json) as f:
                wdc_historic_data = json.load(f)

        driver_string = ""
        cnt = 1
        for driver in sorted(wdc_probabilities, key=wdc_probabilities.get, reverse=True):
            try: 
                prev_driver_probability = wdc_historic_data[yesterday_datetime]
                prev_driver_change = round(((wdc_probabilities[driver] - prev_driver_probability[str(driver)]) / abs(prev_driver_probability[str(driver)])) * 100, 1)

                if prev_driver_change > 0:
                    prev_driver_change = "(+" + str(prev_driver_change) + "%)"
                else:
                    prev_driver_change = "(" + str(prev_driver_change) + "%)"

            except KeyError: 
                prev_driver_change = "(" + str(math.nan) + ")"

            driver_string += num2words(cnt, to='ordinal_num') + " | " + str(driver) + " | " + str(wdc_probabilities[driver]) + " " + prev_driver_change + "\n"
            cnt += 1
        return driver_string


    def construct_daily_teams_str(self, wcc_probabilities):
        yesterday_datetime = (datetime.datetime.utcnow() - datetime.timedelta(1)).strftime("%Y-%m-%d")
        if os.path.exists(self.world_constructors_champion_json):
            with open(self.world_constructors_champion_json) as f:
                wcc_historic_data = json.load(f)

        team_string = ""
        cnt = 1
        for team in sorted(wcc_probabilities, key=wcc_probabilities.get, reverse=True):
            try: 
                prev_team_probability = wcc_historic_data[yesterday_datetime]
                prev_team_change = round(((wcc_probabilities[team] - prev_team_probability[str(team)]) / abs(prev_team_probability[str(team)])) * 100, 1)

                if prev_team_change > 0:
                    prev_team_change = "(+" + str(prev_team_change) + "%)"
                else:
                    prev_team_change = "(" + str(prev_team_change) + "%)"

            except KeyError: 
                prev_team_change = "(" + str(math.nan) + ")"

            team_string += num2words(cnt, to='ordinal_num') + " | " + str(team) + " | " + str(wcc_probabilities[team]) + " " + prev_team_change + "\n"
            cnt += 1
        return team_string
