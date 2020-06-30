import main

betfair=main.BetFairAPI()

def price_to_probability_list(market_id, price_data):
    market_data=betfair.get_runners_market_data(market_id, price_data)
    price_only_df=market_data['Last Price Traded']
    price_only_list=price_only_df.tolist()
    probability_only_list = [(1/x) * 100 for x in price_only_list]
    probability_only_list_2dp = [ round(elem, 2) for elem in probability_only_list ]
    total_probability=(sum(probability_only_list_2dp[0:len(probability_only_list_2dp)-2]))
    print(probability_only_list_2dp)

print(price_to_probability_list(1.164937202, 'SP_TRADED'))