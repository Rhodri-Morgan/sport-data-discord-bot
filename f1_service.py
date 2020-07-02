import f1_betting_collector
import f1_data_processor
import sched, time
import datetime


f1_betting_collector = f1_betting_collector.F1BettingCollector()
f1_data_processor = f1_data_processor.F1DataProcessor()


daily_breakdown_timeout = 30                      # Check whether to post daily breakdown every 30 seconds 
daily_breakdown_posted = False                                                   


def daily_breakdown(sc, daily_breakdown_posted):
    ''' At 1200 UTC saves probabilities for winner of the drivers championship and perpares data for posting'''
    current_datetime_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    current_time = datetime.datetime.strptime(current_datetime_str[11:-3], "%H:%M")
    
    if not daily_breakdown_posted and current_time == datetime.datetime.strptime("12:00","%H:%M"):
        daily_breakdown_posted = True
        current_datetime_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        world_drivers_champion_probabilities = f1_betting_collector.get_championship_outright_winner_probabilities()['Winner - Drivers Championship']
        f1_data_processor.save_world_drivers_champion_data({current_datetime_str[:10] : world_drivers_champion_probabilities})
        # Now ready for more complex analysis and posting to discord
    elif current_time == datetime.datetime.strptime("00:00","%H:%M"):
        daily_breakdown_posted = False
    
    s.enter(daily_breakdown_timeout, 1, daily_breakdown, (sc, daily_breakdown_posted))


s = sched.scheduler(time.time, time.sleep)
s.enter(daily_breakdown_timeout, 1, daily_breakdown, (s, daily_breakdown_posted))
s.run()
