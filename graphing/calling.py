import json
import os
import graphing_func

world_constructors_champion_json = os.path.join(os.getcwd(), 'historic_data/world_constructors_champion.json')
world_drivers_champion_json = os.path.join(os.getcwd(), 'historic_data/world_drivers_champion.json')

with open(world_drivers_champion_json) as f:
    world_drivers_champion_data = json.load(f)

graphing_func = graphing_func.graphing_func()
graphing_func.stackplot(world_drivers_champion_data, 'World Champion Probability', 'Date', 'Win Probability %')
graphing_func.piechart(world_drivers_champion_data, 'World Champion Probability')