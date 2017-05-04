import logging.config
import os

from configs.configuration import Configuration
from stock.us.stock_history_prices import StockHistoryPrices
from stock.us.stock_listings import StockListings
from stock.us.strategy_executor import StrategyExecutor

if __name__ == '__main__':
    # init logging
    os.makedirs('logs', exist_ok=True)
    logging.config.dictConfig(Configuration.get_logging_config())

    # refresh stock lists
    stock_listings = StockListings()
    # stock_listings.refresh()

    # refresh stock prices
    stock_history_prices = StockHistoryPrices()
    # stock_history_prices.refresh()

    # run us stock strategies
    strategy_executor = StrategyExecutor()
    strategy_executor.run()
