from utility.utility import *


class StockMarket:
    def __init__(self, market: Market):
        self.market = market.value

    def refresh_listing(self, excel_file=''):
        raise NotImplemented("Not Implemented in %", type(self).__name__)

    def refresh_stocks(self):
        raise NotImplemented("Not Implemented in %", type(self).__name__)

    def run_strategies(self):
        raise NotImplemented("Not Implemented in %", type(self).__name__)
