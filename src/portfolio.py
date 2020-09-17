import numpy as np

from pandas import DataFrame
from typing import Tuple
from typing import List
from typing import Optional
from typing import Iterable


from stock_frame import StockFrame
from td.client import TDClient


class Portfolio():

    def __init__(self, account_number: str = None):

        self.positions = {}
        self.positions_count = 0
        self.market_value = 0.0
        self.profit_loss = 0.0
        self.risk_tolerance = 0.0
        self.account_number = account_number

# Ownership status =================================================================

    def get_ownership_status(self, symbol: str) -> bool:

        if self.in_portfolio(symbol=symbol) and self.positions[symbol]['ownership_status']:
            return self.positions[symbol]['ownership_status']
        else:
            return False

    def set_ownership_status(self, symbol: str, ownership: bool) -> None:

        if self.in_portfolio(symbol=symbol) and self.positions[symbol]['ownership_status']:
            self.positions[symbol]['ownership_status'] = ownership
        else:
            raise KeyError(
                "Can't set ownership status, as you do not have the symbol in your portfolio."
            )

    def add_position(self, symbol: str, asset_type: str, purchase_date: Optional[str], quantity: int = 0, purchase_price: float = 0.0):
        self.positions[symbol] = {}
        self.positions[symbol]['symbol'] = symbol
        self.positions[symbol]['quantity'] = quantity
        self.positions[symbol]['purchase_date'] = purchase_date
        self.positions[symbol]['purchase_price'] = purchase_price
        self.positions[symbol]['asset_type'] = asset_type

        return self.positions

    def add_positions(self, positions: List[dict]) -> dict:

        if isinstance(positions, list):
            for position in positions:

                self.add_position(
                    symbol=position['symbol'],
                    asset_type=position['asset_type'],
                    purchase_date=position.get('purchase_date', None),
                    purchase_price=position.get('purchase_price', 0.0),
                    quantity=position.get('quantity', 0)
                )

            return self.positions
        else:
            raise TypeError("Positions must be a list of dictionaries")

    def remove_positons(self, symbol: str) -> Tuple[bool, str]:

        if symbol in self.positions:
            del self.positions[symbol]
            return (True, "{Symbol} was successfully removed.".format(symbol=symbol))
        else:
            return (False, "{Symbol} did not exist in the portfolio".format(symbol=symbol))

    def in_portfolio(self, symbol: str) -> bool:
        if symbol in self.positions:
            return True
        else:
            return False

    def is_profitable(self, symbol: str, current_price: float) -> bool:

        # grab purchase price
        purchase_price = self.positions[symbol]['purchase_price']

        if (purchase_price <= current_price):
            return True
        elif (purchase_price >= current_price):
            return False

    @property
    def td_client(self) -> TDClient:

        # returns TDClient -- authenticated session with TD API

        return self._td_client

    @td_client.setter
    def td_client(self, td_client: TDClient) -> None:

        # arguements: td_client - authenticated session with TD API

        self._td_client: TDClient = td_client

    def total_allocation(self):
        pass

    def risk_exposure(self):
        pass

    def total_market_value(self):
        pass

    def _grab_daily_historical_prices(self) -> StockFrame:

        new_prices = []

        # Loop through each position.
        for symbol in self.positions:

            # Grab the historical prices.
            historical_prices_response = self.td_client.get_price_history(
                symbol=symbol,
                period_type='year',
                period=1,
                frequency_type='daily',
                frequency=1,
                extended_hours=True
            )

            # Loop through the candles.
            for candle in historical_prices_response['candles']:

                new_price_mini_dict = {}
                new_price_mini_dict['symbol'] = symbol
                new_price_mini_dict['open'] = candle['open']
                new_price_mini_dict['close'] = candle['close']
                new_price_mini_dict['high'] = candle['high']
                new_price_mini_dict['low'] = candle['low']
                new_price_mini_dict['volume'] = candle['volume']
                new_price_mini_dict['datetime'] = candle['datetime']
                new_prices.append(new_price_mini_dict)

        # Create and set the StockFrame
        self._stock_frame_daily = StockFrame(data=new_prices)
        self._stock_frame_daily.create_frame()

        return self._stock_frame_daily
