import numpy as np
import pandas as pd

from typing import Union
from typing import Dict
from typing import List
from datetime import timezone
from datetime import time
from datetime import datetime

from pandas.core.groupby import DataFrameGroupBy
from pandas.core.window import RollingGroupby


class StockFrame():

    def __init__(self, data: List[dict]) -> None:
        self._data = data
        self._frame: pd.DataFrame = self.create_frame()
        self._symbol_groups: DataFrameGroupBy = None
        self._symbol_rolling_groups: RollingGroupby = None

    @property
    def frame(self) -> pd.DataFrame:
        return self._frame

    @property
    def symbol_groups(self) -> DataFrameGroupBy:

        self._symbol_groups: DataFrameGroupBy = self._frame.groupby(
            by='symbol',
            as_index=False,
            sort=True
        )

        return self._symbol_groups

    def symbol_rolling_groups(self, size: int) -> RollingGroupby:

        if not self._symbol_groups:
            self.symbol_groups

        self._symbol_rolling_groups = self.symbol_groups.rolling(size)

        return self.symbol_rolling_groups

    def create_frame(self) -> pd.DataFrame:

        # make data frame
        price_df = pd.DataFrame(data=self._data)
        price_df = self._parse_datetime_column(price_df=price_df)
        price_df = self._set_multi_index(price_df=price_df)
        return price_df

    def _parse_datetime_column(self, price_df: pd.DataFrame) -> pd.DataFrame:
        price_df['datetime'] = pd.to_datetime(
            price_df['datetime'], unit='ms', origin='unix')

        return price_df

    def _set_multi_index(self, price_df: pd.DataFrame) -> pd.DataFrame:

        price_df = price_df.set_index(keys=['symbol', 'datetime'])

        return price_df

    def add_rows(self, data: dict) -> None:

        column_names = ['open', 'close', 'high', 'low', 'volume']

        for quote in data:

            # parse timestamp
            time_stamp = pd.to_datetime(
                quote['datetime'],
                unit='ms',
                origin='unix',
            )
            # define the index
            row_id = (quote['symbol'], time_stamp)

            # Define the Values
            row_values = [
                quote['open'],
                quote['close'],
                quote['high'],
                quote['low'],
                quote['volume']
            ]

            # create new row
            new_row = pd.Series(data=row_values)

            # add the row
            self.frame.loc[row_id, column_names] = new_row.values
            self.frame.sort_index(inplace=True)

    def do_indicator_exist(self, column_names: List[str]) -> bool:

        if set(column_names).issubset(self._frame.columns):
            return True
        else:
            raise KeyError("The following indicator columns are missing from the StockFrame: {missing_columns}".format(
                missing_columns=set(column_names).difference(
                    self._frame.columns)
            ))

    def _check_signals(self, indicators: dict, indciators_comp_key: List[str], indicators_key: List[str]) -> Union[pd.DataFrame, None]:

        # Grab the last rows.
        last_rows = self._symbol_groups.tail(1)

        # Define a list of conditions.
        conditions = []

        # Check to see if all the columns exist.
        if self.do_indicator_exist(column_names=indicators_key):

            for indicator in indicators_key:

                column = last_rows[indicator]

                buy_condition_target = indicators[indicator]['buy']
                sell_condition_target = indicators[indicator]['sell']

                buy_condition_operator = indicators[indicator]['buy_operator']
                sell_condition_operator = indicators[indicator]['sell_operator']

                condition_1: pd.Series = buy_condition_operator(
                    column, buy_condition_target
                )
                condition_2: pd.Series = sell_condition_operator(
                    column, sell_condition_target
                )

                condition_1 = condition_1.where(lambda x: x == True).dropna()
                condition_2 = condition_2.where(lambda x: x == True).dropna()

                conditions.append(('buys', condition_1))
                conditions.append(('sells', condition_2))

        check_indicators = []

        for indicator in indciators_comp_key:
            parts = indicator.split('_comp_')
            check_indicators += parts

        if self.do_indicator_exist(column_names=check_indicators):

            for indicator in indciators_comp_key:

                # Split the indicators.
                parts = indicator.split('_comp_')

                # Grab the indicators that need to be compared.
                indicator_1 = last_rows[parts[0]]
                indicator_2 = last_rows[parts[1]]

                if indicators[indicator]['buy_operator']:
                    buy_condition_operator = indicators[indicator]['buy_operator']

                    condition_1: pd.Series = buy_condition_operator(
                        indicator_1, indicator_2
                    )

                    condition_1 = condition_1.where(
                        lambda x: x == True).dropna()
                    conditions.append(('buys', condition_1))

                if indicators[indicator]['sell_operator']:
                    sell_condition_operator = indicators[indicator]['sell_operator']

                    condition_2: pd.Series = sell_condition_operator(
                        indicator_1, indicator_2
                    )

                    condition_2 = condition_2.where(
                        lambda x: x == True).dropna()
                    conditions.append(('sells', condition_2))

        return conditions
