![Banner Image](documentation_sources/banner.png)

# Sport Data Discord Bot

Sport is an interesting and thrilling experience where anything can happen. Part of the overall appeal of sport is this possibility of change and with that also seeing how others react and judging what they think will happen. The purpose of this Discord bot is to make sporting probability information more easily accessible through Discord for all sport lovers across many different sports from Soccer to Snooker and plenty in between.

https://user-images.githubusercontent.com/52254823/150962277-5a26d873-2c7b-4518-9f87-6346320a8595.mp4

# Methodologies: 

This bot utilises a few different services and APIs to transmit sporting data over the popular communication method [Discord](https://discord.com/). Firstly and most importantly, data is collected using the [BetFair API using betfairlightweight](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+API). This API allows us to query data across many different sports with an even wider range of events and markets for different items such who will score first? Using the last price traded we are able to assign each runner a percentage chance of winning (given there is enough market data). This data collected from BetFair is then selected, formatted and transmitted using [discord.py](https://discordpy.readthedocs.io/en/latest/index.html) an 'async ready API wrapper for Discord'. Finally we use the [AWS S3](https://aws.amazon.com/s3/) for downloading and uploading users recent commands (such that they are preserved in the event of some crash/restart).

# Data Sources: 

This bot utilises live [BetFair Exchange](https://www.betfair.com.au/exchange/plus/) betting data.

For this bot to function correctly we collect some data from the users such as their last valid request. With this in mind we have created the means for the user to view their data `!my_data` and further more delete it from storage `!delete_data`.

# Status:

Currently the Sport Data Discord Bot is being hosted using the [Heroku](https://www.heroku.com/) service. You can test it out for yourself by adding it to your server through this [invite link](https://discord.com/api/oauth2/authorize?client_id=877412844398837800&permissions=0&scope=bot) and messaging `!commands` to it in PMs.
