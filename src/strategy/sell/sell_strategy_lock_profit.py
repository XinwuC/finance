import pandas
from utility.data_utility import DataUtility
from utility.utility import *
from zipline.finance.execution import ExecutionStyle, StopLimitOrder


class SimpleProfitLockSellStrategy:
    def __init__(self):
        self.minimal_profit = 0.05
        pass

    def get_sell_price(self, price_history: pandas.DataFrame,
                       target_date: datetime.date = None) -> float:
        price_history, target_date = DataUtility.calibrate_price_history(price_history, target_date)
        price_history.loc[:, 'daily_range_pct'] = (price_history[StockPriceField.High.value] - price_history[
            StockPriceField.Low.value]) / price_history[StockPriceField.Low.value]
        sell_price = price_history[StockPriceField.Low.value][target_date] * (
        1 - price_history['daily_range_pct'].mean())
        return sell_price

    def get_sell_order(self, profit_lock_price: float, cost_basis: float,
                       previous_lock_price: float = 0) -> ExecutionStyle:
        minimal_sell_price = cost_basis * (1 + self.minimal_profit)
        order = None
        if profit_lock_price >= minimal_sell_price and profit_lock_price > previous_lock_price:
            order = StopLimitOrder(limit_price=profit_lock_price, stop_price=profit_lock_price)
        return order
