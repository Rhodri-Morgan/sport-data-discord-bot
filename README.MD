![Banner Image](documentation_sources/banner.png)

# Sport Data Discord Bot

*See [BACKGROUND.MD](BACKGROUND.MD) for example, motivation, data sources and methodology.*

## Python and Dependencies

### Python Version

This project is using `Python 3.6.0`.

### Dependencies
 
The list of dependencies for this project can be found in `requirements.txt` and can be installed using `pip install -r requirements.txt`. To build a new `requirements.txt` delete the old version, navigate to directory and run `pip freeze > requirements.txt`.

## Running

### Heroku

The project is currently deployed on [Heroku](https://www.heroku.com/) and connected to this repository. Pushing to the `master` branch will automatically cause the bot to refresh with the changes applied.

**`procfile` and  `runtime` are essential Heroku files. Do not modify or remove them.**

As seen throughout the scripts, keys and secrets are all stored on Heroku in the environment variables section. 

### Discord

You can access and use the bot by visiting [this link](https://discord.com/api/oauth2/authorize?client_id=877412844398837800&permissions=0&scope=bot) and adding it to your server. Message it `!commands` in PMs to get usage instructions.
