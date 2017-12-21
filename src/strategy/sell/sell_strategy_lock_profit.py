import pandas

from utility.data_utility import DataUtility
from utility.utility import *


class SimpleProfitLockSellStrategy:
    def __init__(self, mini_profit: float = 0.05):
        self.minimal_profit = mini_profit
        pass

    def get_sell_price(self, price_history: pandas.DataFrame,
                       target_date: datetime.date = None) -> float:
        price_history, target_date = DataUtility.calibrate_price_history(price_history, target_date)
        price_history.is_copy = False
        price_history['daily_range_pct'] = (price_history[StockPriceField.High.value] - price_history[
            StockPriceField.Low.value]) / price_history[StockPriceField.Low.value]
        sell_price = price_history[StockPriceField.Low.value][target_date] * (
                1 - price_history['daily_range_pct'].mean())
        return sell_price
