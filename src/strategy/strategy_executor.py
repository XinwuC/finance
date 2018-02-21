import logging.config
import re

import pandas

from strategy.strategy import Strategy
from utility.data_utility import DataUtility
from utility.utility import *


class StrategyExecutor:
    def __init__(self, market: Market):
        self.logger = logging.getLogger(__name__)
        self.configs = Utility.get_config(market)
        self.strategies = []
        for strategy_name in self.configs.strategy.list:
            strategy = Strategy.get_strategy(strategy_name, self.configs.strategy)
            if strategy is not None:
                self.strategies.append(strategy)
                self.logger.info("Strategy %s added for market %s" % (strategy.name, market.value))
            else:
                self.logger.error("Cannot find Strategy %s for market %s" % (strategy_name, market.value))
        # set history folder
        self.history_folder = Utility.get_data_folder(market=market, folder=DataFolder.Stock_History)

    def run(self, stock_list: [] = [], target_date: datetime.date = None):
        buying_options = {}
        for strategy in self.strategies:
            result = self._run_strategy(strategy, stock_list, target_date)
            if result is not None and not result.empty:
                buying_options[strategy.name] = result
                with pandas.option_context('display.max_rows', 10, 'expand_frame_repr', False):
                    self.logger.info('%s analysis results:\n%s' % (strategy.name, result))
        return buying_options

    def _run_strategy(self, strategy, stock_list: [] = [], target_date: datetime.date = None) -> pandas.DataFrame:
        with os.scandir(self.history_folder) as it:
            name_pattern = re.compile(r'\w+.csv')
            name_extractor = re.compile(r'\w+')
            result = None  # pandas.DataFrame()
            for entry in it:
                if entry.is_file() and name_pattern.match(entry.name):
                    symbol, _ = name_extractor.findall(entry.name)
                    if stock_list and symbol not in stock_list:
                        continue  # skip symbol that is not in target stock list.
                    prices = pandas.read_csv(entry.path, index_col=0, parse_dates=True)
                    # validate prices schema is correct
                    if not DataUtility.validate_price_history(prices):
                        self.logger.error('Corrupt price history file %s, skip.' % entry.path)
                        continue
                    self.logger.info('Running strategy %s for [%s]' % (strategy.name, symbol))
                    buying_symbol = strategy.analysis(prices, target_date)
                    if buying_symbol is not None:
                        if result is None:
                            result = pandas.DataFrame(buying_symbol).T
                        else:
                            result = result.append(buying_symbol, ignore_index=True)
            return result
