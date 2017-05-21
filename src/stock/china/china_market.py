import logging

import pandas
import tushare as ts
from pandas import ExcelWriter

from stock.stock_market import StockMarket
from strategy.strategy_executor import StrategyExecutor
from utility.utility import *


class ChinaMarket(StockMarket):
    def __init__(self):
        super(ChinaMarket, self).__init__(Market.China)
        self.logger = logging.getLogger(__name__)
        self.strategy_executor = StrategyExecutor(Market.China)

    def refresh_listing(self, excel_file=Utility.get_stock_listing_xlsx(Market.China)):
        """
        refresh stock listings
        :return: Void
        """
        try:
            with ExcelWriter(excel_file) as writer:
                self.logger.info("Refreshing stock listings on China market...")
                listings = ts.get_stock_basics()
                # normalize the listing fields
                listings.index.rename(ListingField.Symbol.value, inplace=True)
                listings.rename(columns={'name': ListingField.Name.value,
                                         'timeToMarket': ListingField.IPO.value,
                                         'industry': ListingField.Industry.value
                                         }, index=str, inplace=True)
                listings.to_excel(writer, Market.China.value)
                self.logger.info('Saved stock listings to %s', excel_file)
        except Exception as e:
            self.logger.error('Fetching stock listings error for China market: %s', e)

    def refresh_stocks(self):
        with pandas.ExcelFile(Utility.get_stock_listing_xlsx(Market.China, latest=True)) as listings_file:
            listings = pandas.read_excel(listings_file, Market.China.value,
                                         dtype={ListingField.Symbol.value: str},
                                         parse_dates=[ListingField.IPO.value],
                                         date_parser=lambda x: pandas.to_datetime(str(x)) if len(
                                             str(x)) == 8 else pandas.to_datetime(
                                             Utility.get_config().history_start_date))

            total_symbols = 0
            symbols_no_data = 0
            for stock in listings.itertuples():
                total_symbols += 1
                history_prices = self.refresh_stock(stock.Symbol, stock.IPO)
                if history_prices is not None and not history_prices.empty:
                    history_prices.to_csv(Utility.get_stock_price_history_file(
                        Market.China, stock.Symbol, stock.IPO.year))
                    self.logger.info('Updated price history for [%s] (%s) %s, IPO %s', stock.Industry, stock.Symbol,
                                     stock.Name, stock.IPO.date())
                else:
                    symbols_no_data += 1
                    self.logger.warning('Failed to get price history for [%s] (%s) %s, IPO %s', stock.Industry,
                                        stock.Symbol, stock.Name, stock.IPO.date())
            self.logger.error(
                'Stock prices update completed, %s (%s) symbols has no data.', symbols_no_data, total_symbols)

    @staticmethod
    def refresh_stock(symbol: str, start_date: datetime, end_date=datetime.date.today()):
        history_prices = ts.get_k_data(code=symbol, start=start_date.isoformat(), end=end_date.isoformat())
        if history_prices is not None and not history_prices.empty:
            del history_prices['code']
            history_prices.rename(columns={'date': StockPriceField.Date.value,
                                           'open': StockPriceField.Open.value,
                                           'close': StockPriceField.Close.value,
                                           'high': StockPriceField.High.value,
                                           'low': StockPriceField.Low.value,
                                           'volume': StockPriceField.Volume.value}, index=str, inplace=True)
            history_prices.set_index(StockPriceField.Date.value, inplace=True, verify_integrity=True)
            history_prices.sort_index(inplace=True, ascending=False)
            history_prices[StockPriceField.AdjustPrice.value] = history_prices[StockPriceField.Close.value]
            history_prices["adjusted_change_percentage"] = history_prices[StockPriceField.Close.value] / history_prices[
                StockPriceField.Close.value].shift(-1) - 1
        return history_prices

    def run_strategies(self):
        return self.strategy_executor.run()
