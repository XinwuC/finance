import datetime
import logging.config
import os
import re

import pandas

from configs.configuration import Configuration
from strategy.strategy import Strategy


class StrategyExecutor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.configs = Configuration.get_us_config()
        self.strategies = []
        for strategy_name in self.configs.strategy.list:
            strategy = Strategy.get_strategy(strategy_name, self.configs.strategy)
            if strategy is not None:
                self.strategies.append(strategy)
                self.logger.info("Strategy %s added." % strategy.name)
            else:
                self.logger.error("Cannot find Strategy %s" % strategy_name)
        self.history_folder = os.path.join(self.configs.data_path, self.configs.data_history_folder)

    def run(self):
        buying_options = {}
        for strategy in self.strategies:
            result = self._run_strategy(strategy)
            if result is not None and not result.empty:
                buying_options[strategy.name] = result
                with pandas.option_context('display.max_rows', 10, 'expand_frame_repr', False):
                    self.logger.debug('%s analysis results:\n%s' % (strategy.name, result))
        return buying_options

    def _run_strategy(self, strategy) -> pandas.DataFrame:
        with os.scandir(self.history_folder) as it:
            name_pattern = re.compile(r'\w+-\w+.csv')
            name_extractor = re.compile(r'\w+')
            result = None  # pandas.DataFrame()
            for entry in os.scandir(self.history_folder):
                if entry.is_file() and name_pattern.match(entry.name):
                    (market, symbol, dummy) = name_extractor.findall(entry.name)
                    prices = pandas.read_csv(entry.path, index_col=0, parse_dates=True)
                    self.logger.info('Running strategy %s for [%s] %s' % (strategy.name, market, symbol))
                    buying_symbol = strategy.analysis(market, symbol, prices)
                    if buying_symbol is not None:
                        if result is None:
                            result = pandas.DataFrame(buying_symbol).T
                        else:
                            result = result.append(buying_symbol, ignore_index=True)
            return result
