from strategy.strategy_executor import StrategyExecutor
from utility.utility import *


class StockMarket:
    def __init__(self, market: Market):
        self.market = market.value
        self.strategy_executor = StrategyExecutor(market)

    def refresh_listing(self, excel_file=''):
        raise NotImplemented("Not Implemented in %", type(self).__name__)

    def refresh_stocks(self, stock_list: [] = []):
        raise NotImplemented("Not Implemented in %", type(self).__name__)

    def run_strategies(self, stock_list: [] = []):
        return self.strategy_executor.run(stock_list)
