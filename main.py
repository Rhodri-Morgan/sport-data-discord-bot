import betfairlightweight
from betfairlightweight import filters
import pandas as pd
import numpy as np
import os
import datetime
import json


# Setting up credentials and certifications
certifications = os.path.join(os.getcwd(), 'certifications')

with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
  credentials = json.loads(f.read())

# Validating interaction with API
trading = betfairlightweight.APIClient(username=credentials['username'],
                                       password=credentials['password'],
                                       app_key=credentials['app_key'],
                                       certs=certifications)

trading.login()

# Interact with the trading object.

trading.logout()