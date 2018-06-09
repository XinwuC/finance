import re
from abc import abstractmethod

from stock.stock import Stock
from utility.utility import *


class Screener:
    @abstractmethod
    def screen(self, stock: Stock) -> bool:
        return NotImplemented


class NameScreener(Screener):
    def __init__(self, config):
        self._regex = re.compile(config.excludes, re.IGNORECASE)

    def screen(self, stock: Stock) -> bool:
        return stock is None or self._regex.search(stock.name) is None


class PennyStockScreener(Screener):
    def screen(self, stock: Stock) -> bool:
        if stock is None or not isinstance(stock.price, pd.DataFrame) or stock.price.empty:
            return True
        if not DataUtility.validate_price_history(stock.price):
            return False
        return stock.price[StockPriceField.Low.value][-1] > 1
