import json
import os


world_constructors_champion_json = os.path.join(os.getcwd(), 'historic_data/world_constructors_champion.json')
world_drivers_champion_json = os.path.join(os.getcwd(), 'historic_data/world_drivers_champion.json')


def save_world_constructors_champion_data(world_constructors_champion_probabilities):
    ''' Saves world constructors champion probability data to JSON file in historic_data directory '''
    if not os.path.exists(world_constructors_champion_json):
        with open(world_constructors_champion_json, 'w') as f:
            json.dump(world_constructors_champion_probabilities, f)
    else:
        with open(world_constructors_champion_json) as f:
            world_constructors_champion_data = json.load(f)
        world_constructors_champion_merged = {**world_constructors_champion_data, **world_constructors_champion_probabilities}
        with open(world_constructors_champion_json, 'w') as f:
            json.dump(world_constructors_champion_merged, f)


def save_world_drivers_champion_data(world_drivers_champion_probabilities):
    ''' Saves world drivers champion probability data to JSON file in historic_data directory '''
    if not os.path.exists(world_drivers_champion_json):
        with open(world_drivers_champion_json, 'w') as f:
            json.dump(world_drivers_champion_probabilities, f)
    else:
        with open(world_drivers_champion_json) as f:
            world_drivers_champion_data = json.load(f)
        world_drivers_champion_merged = {**world_drivers_champion_data, **world_drivers_champion_probabilities}
        with open(world_drivers_champion_json, 'w') as f:
            json.dump(world_drivers_champion_merged, f)