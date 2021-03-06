from configparser import ConfigParser
from datetime import timedelta
from datetime import datetime
import pandas as pd
import operator
import pathlib
import pprint
import time as true_time

from robot import PyRobot
from indicators import Indicators


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
# pprint.pprint(new_positions)

# add a single position to the portfolio
trading_robot.portfolio.add_position(
    symbol='MSFT',
    quantity=10,
    purchase_price=10.00,
    asset_type='equity',
    purchase_date='2020-04-01'
)

# test addition of positions
# pprint.pprint(trading_robot.portfolio.positions)

# Check to see if market open (testing)
if trading_robot.regular_market_open:
    print('Market Open')
else:
    print('Market Closed')


if trading_robot.pre_market_open:
    print('Pre-Market Open')
else:
    print('Pre-Market Closed')

if trading_robot.post_market_open:
    print('Post-Market Open')
else:
    print('Post-Market Closed')

# Grab quotes in our portfolio
current_quotes = trading_robot.grab_current_quotes()
# pprint.pprint(current_quotes)

# Define date range
end_date = datetime.today()
start_date = end_date - timedelta(days=30)

# grab historical prices
historical_prices = trading_robot.grab_historical_prices(
    start=start_date,
    end=end_date,
    bar_size=1,
    bar_type='minute'
)

# Convert data into a Stockframe (multi index dataframe)
stock_frame = trading_robot.create_stock_frame(
    data=historical_prices['aggregated'])

pprint.pprint(stock_frame.frame.head(n=20))

# Create a Trade object
new_trade = trading_robot.create_trade(
    trade_id='long_msft',
    enter_or_exit='enter',
    long_or_short='long',
    order_type='lmt',
    price=150.00
)

# make GTD
new_trade.good_till_cancel(cancel_time=datetime.now() + timedelta(minutes=90))

# Change session
new_trade.modify_session(session='am')

# Add an Order leg
new_trade.instrument(
    symbol='MSFT',
    quantity=2,
    asset_type='EQUITY'
)

# Add a stop loss
new_trade.add_stop_loss(
    stop_size=.10,
    percentage=False
)

# pprint.pprint(new_trade.order)

indicator_client = Indicators(price_data_frame=stock_frame)

indicator_client.rsi(period=14)

indicator_client.sma(period=200)

indicator_client.ema(period=50)

indicator_client.set_indicator_signals(
    indicator='rsi',
    buy=40.0,
    sell=20.0,
    condition_buy=operator.ge,
    condition_sell=operator.le
)

trades_dict = {
    'MSFT': {
        'trade_func': trading_robot.trades['long_msft'],
        'trade_id': trading_robot.trades['long_msft'].trade_id
    }
}


while True:

    latest_bars = trading_robot.get_latest_bar()

    stock_frame.add_rows(data=latest_bars)

    # refresh indicators
    indicator_client.refresh()

    print("="*50)
    print("Current Stock Frame")
    print("-"*50)
    print(stock_frame.symbol_groups.tail())
    print("-"*50)
    print("")

    # check signals
    signals = indicator_client.check_signals()

    # how to execute trades
    #trading_robot.execute_signals(signals=signals, trades_to_execute=trades_dict)

    # grab last bar, this is after adding new rows
    last_bar_timestamp = trading_robot.stock_frame.frame.tail(
        1).index.get_level_values(1)

    # wait till next bar
    trading_robot.wait_till_next_bar(last_bar_timestamp=last_bar_timestamp)
