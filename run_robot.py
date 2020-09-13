import time as true_time
import pprint
import pathlib
import operator
import pandas as pd

from datetime import datetime
from datetime import timedelta
from configparser import ConfigParser

from pyrobot.robot import PyRobot
from pyrobot.indicators import Indicators

# Grab the config file values.
config = ConfigParser()
config.read('configs/config.ini')

CLIENT_ID = config.get('main', 'CLIENT_ID')
REDIRECT_URI = config.get('main', 'REDIRECT_URI')
CREDENTIALS_PATH = config.get('main', 'JSON_PATH')
ACCOUNT_NUMBER = config.get('main', 'ACCOUNT_NUMBER')

# Initialize robot
trading_robot = PyRobot(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, paper_trading=True,
                        credentials_path=CREDENTIALS_PATH, trading_account=ACCOUNT_NUMBER)

# Creating a portfolio
trading_robot_portfolio = trading_robot.create_portfolio()


# Add positions in our portfolio
multi_positions = [
    {
        'asset_type': 'equity',
        'quantity': 2,
        'purchase_price': 4.00,
        'symbol': 'TSLA',
        'purchase_date': '2020-01-31'
    },
    {
        'asset_type': 'equity',
        'quantity': 2,
        'purchase_price': 4.00,
        'symbol': 'SQ',
        'purchase_date': '2020-01-31'
    }
]

# add positions to the portfolio
new_positions = trading_robot.portfolio.add_positions(
    positions=multi_positions)

# test authorization for td api
pprint.pprint(new_positions)
