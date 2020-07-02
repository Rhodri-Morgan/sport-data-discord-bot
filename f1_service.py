import f1_betting_collector
import f1_data_processor
import sched, time
import datetime
import os
import json


f1_betting_collector = f1_betting_collector.F1BettingCollector()
f1_data_processor = f1_data_processor.F1DataProcessor()


daily_breakdown_timeout = 30                      # Check whether to post daily breakdown every 30 seconds 
daily_breakdown_posted = False                                                   


def daily_breakdown(sc, daily_breakdown_posted):
    ''' At 1200 UTC saves probabilities for winner of the drivers and constructors championship and packages for discord post'''
    current_datetime_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    current_time = datetime.datetime.strptime(current_datetime_str[11:-3], "%H:%M")
    
    if not daily_breakdown_posted and current_time == datetime.datetime.strptime("12:00","%H:%M"):
        daily_breakdown_posted = True

        world_drivers_champion_probabilities = f1_betting_collector.get_championship_outright_winner_probabilities()['Winner - Drivers Championship']
        world_constructors_champion_probabilities = f1_betting_collector.get_championship_outright_winner_probabilities()['Winner - Constructors Championship']

        f1_data_processor.save_world_drivers_champion_data({current_datetime_str[:10] : world_drivers_champion_probabilities})
        f1_data_processor.save_world_constructors_champion_data({current_datetime_str[:10] : world_constructors_champion_probabilities})

        daily_drivers_string = f1_data_processor.construct_daily_drivers_str(world_drivers_champion_probabilities)
        daily_team_string = f1_data_processor.construct_daily_teams_str(world_constructors_champion_probabilities)
        daily_strings = {"message" : "TEST - Formula 1 Daily Update @ 1200 UTC\n" + daily_drivers_string + "\n" + daily_team_string}

        temp_path = os.path.join(os.getcwd(), "temp")
        os.mkdir(temp_path)
        with open(os.path.join(temp_path, "send.json"), 'w') as f:
            json.dump(daily_strings, f)
        os.rename(temp_path, os.path.join(os.getcwd(), "temp_f1_daily_update"))

    elif current_time == datetime.datetime.strptime("00:00","%H:%M"):
        daily_breakdown_posted = False
    
    s.enter(daily_breakdown_timeout, 1, daily_breakdown, (sc, daily_breakdown_posted))


s = sched.scheduler(time.time, time.sleep)
s.enter(daily_breakdown_timeout, 1, daily_breakdown, (s, daily_breakdown_posted))
s.run()

