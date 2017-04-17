from configs.configuration import Configuration
import logging.config

from stock.us.stock_listings import StockListings
from stock.us.stock_history_prices import StockHistoryPrices

if __name__ == '__main__':
    # init logging
    logging.config.dictConfig(Configuration.get_logging_config())

    # refresh stock lists
    stock_listings = StockListings()
    stock_listings.refresh()

    # refresh stock prices
    stock_history_prices = StockHistoryPrices()
    stock_history_prices.refresh()
