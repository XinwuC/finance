from utility.utility import *


class SimpleProfitLockSellStrategy:
    def __init__(self, mini_profit: float = 0.05):
        self.minimal_profit = mini_profit

    def get_sell_price(self, cost_basis: float, price_history: pd.DataFrame,
                       target_date: datetime.date = None) -> float:
        price_history, target_date = DataUtility.calibrate_price_history(price_history, target_date)
        if price_history is None or price_history.empty:
            return 0
        else:
            daily_range_pct = (price_history[StockPriceField.High.value] - price_history[StockPriceField.Low.value]) / \
                              price_history[StockPriceField.Low.value]
            daily_range_price = price_history[StockPriceField.Low.value][target_date] * (1 - daily_range_pct.mean())
            low_pct = price_history[StockPriceField.Low.value].pct_change()
            low_pct_price = price_history[StockPriceField.Low.value][target_date] * (1 - low_pct.std())
            if min(daily_range_price, low_pct_price) <= cost_basis * (1 + self.minimal_profit):
                return min(daily_range_price, low_pct_price)
            else:
                return max(daily_range_price, low_pct_price)
