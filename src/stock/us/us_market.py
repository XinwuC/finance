"""
Get a full listing symbols.

Source provider is http://www.nasdaq.com/screening/company-list.aspx

"""

import concurrent.futures
import logging
import re
import shutil

import numpy as np
import pandas
import pandas_datareader.data as web
from alpha_vantage.timeseries import TimeSeries
from dateutil.relativedelta import relativedelta

from stock.stock_market import StockMarket
from utility.utility import *


class UsaMarket(StockMarket):
    def __init__(self,
                 provider_url=Utility.get_config(Market.US).stock_list_provider,
                 exchanges=Utility.get_config(Market.US).exchanges,
                 concurrent=Utility.get_config(Market.US).concurrent,
                 retry=Utility.get_config().data_retry,
                 avkey=None):
        super(UsaMarket, self).__init__(Market.US)
        self.logger = logging.getLogger(__name__)
        self.provider_url = provider_url
        self.exchanges = exchanges
        self.concurrent = concurrent
        self.retry = retry
        if avkey is None:
            self.data_sources = []
        else:
            self.alpha_vantage = TimeSeries(key=avkey, retries=retry, output_format='pandas', indexing_type='date')
            self.data_sources = [self._download_AlphaVantage]
        self.data_sources.extend([self._download_morningstar, self._download_quandl, self._download_iex])

    def refresh_listing(self, excel_file=Utility.get_stock_listing_xlsx(Market.US)):
        """
        refresh symbols lists from source provider, and store in sto

        :param excel_file: file name to the stored file, actual file name will append _yyyy-mm-dd.xlsx
        :return: void
        """
        try:
            with pandas.ExcelWriter(excel_file) as writer:
                self.logger.info('Saving stock listings to %s.', excel_file)
                for exchange in self.exchanges:
                    try:
                        listings = pandas.read_csv(self.provider_url % exchange)
                        # normalize the listing fields
                        listings.rename(columns={'Symbol': ListingField.Symbol.value,
                                                 'IPOyear': ListingField.IPO.value,
                                                 'Sector': ListingField.Sector.value,
                                                 'industry': ListingField.Industry.value,
                                                 }, index=str, inplace=True)
                        listings.to_excel(writer, exchange)
                        self.logger.info('Saved stock listings for exchange %s.', exchange.upper())
                    except Exception as e:
                        self.logger.error('Fetching stock listings error for exchange %s: %s', exchange.upper(), e)
        except Exception as e:
            self.logger.exception('Saving stock listings failed: %s', e)

    def refresh_stocks(self, stock_list: [] = []):
        """
        Refresh stock price history. It will first get latest symbols list from the web services provided in configs,
        then fetch stock price history from Yahoo! and Google, Yahoo! data take precedence over Google data.

        The data will store in the target location specified in configs. Each symbol stored in one file, naming as
        %exchange%_%symbol%.csv

        Errors are logged in error.log file.

        :return: None
        """
        total_symbols = 0
        symbols_no_data = 0
        symbol_pattern = re.compile(r'^(\w|\.)+$')
        futures = []
        # purge stock history folder if refresh all (ie. stock_list is empty)
        if not stock_list:
            shutil.rmtree(Utility.get_data_folder(DataFolder.Stock_History, Market.US), ignore_errors=True)
        # concurrent download prices
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent) as executor:
            with pandas.ExcelFile(Utility.get_stock_listing_xlsx(Market.US, latest=True)) as listings:
                for exchange in listings.sheet_names:
                    self.logger.info('Fetching stock history prices from exchange %s.', exchange.upper())
                    stocks = pandas.read_excel(listings, exchange)
                    for stock in stocks.itertuples():
                        if stock_list and stock.Symbol not in stock_list:
                            continue  # skip stock that is not in stock_list
                        if not symbol_pattern.match(stock.Symbol):
                            continue  # skip invalid symbols
                        if isinstance(stock.IPO, str):
                            start_date = Utility.get_config().history_start_date if stock.IPO == 'n/a' else stock.IPO
                        elif np.isnan(stock.IPO):
                            start_date = Utility.get_config().history_start_date
                        else:
                            start_date = str(int(stock.IPO))
                        start_date = pandas.to_datetime(start_date)
                        if self.concurrent > 1:
                            futures.append(executor.submit(self.refresh_stock, stock.Symbol, start_date))
                        else:
                            symbols_no_data += self.refresh_stock(stock.Symbol, start_date) is None
                        total_symbols += 1
        for future in futures:
            symbols_no_data += (future.result() is None)
        self.logger.error('Stock prices update completed, %s (%s) symbols has no data.', symbols_no_data, total_symbols)

    def refresh_stock(self, symbol: str, start_date: datetime, end_date=datetime.datetime.today()):
        history_prices = self.download_data(symbol, start_date, end_date)
        if history_prices is not None:
            history_prices.to_csv(Utility.get_stock_price_history_file(Market.US, symbol))
            self.logger.info('Updated price history for [%s]\t(%s - %s)', symbol, start_date.date(), end_date.date())
        return history_prices

    def download_data(self, symbol: str, start: datetime.datetime, end: datetime.datetime) -> pd.DataFrame:
        data = None
        for download_source in self.data_sources:
            data = download_source(symbol, start, end)
            if data is not None:
                break
        return data

    def _download_AlphaVantage(self, symbol: str, start, end) -> pd.DataFrame:
        data = None
        try:
            data = self.alpha_vantage.get_daily_adjusted(symbol, outputsize='full')[0]
            data = data[['1. open', '2. high', '3. low', '5. adjusted close', '6. volume']]
            data.index.rename(StockPriceField.Date.value, inplace=True)
            data[StockPriceField.Symbol.value] = symbol.strip()
            data.rename(columns={'Symbol': StockPriceField.Symbol.value,
                                 '1. open': StockPriceField.Open.value,
                                 '2. high': StockPriceField.High.value,
                                 '3. low': StockPriceField.Low.value,
                                 '5. adjusted close': StockPriceField.Close.value,
                                 '6. volume': StockPriceField.Volume.value}, inplace=True)
        except Exception as e:
            self.logger.error("Failed to get (%s) price history from AlphaVantage, %s", symbol, e)
        return data

    def _download_morningstar(self, symbol: str, start: datetime.datetime, end: datetime.datetime) -> pd.DataFrame:
        data = None
        try:
            data = web.DataReader(symbol.strip(), 'morningstar', start, end + datetime.timedelta(days=1),
                                  retry_count=self.retry)
            data.reset_index(level=[0], inplace=True)
            data.index.rename(StockPriceField.Date.value, inplace=True)
            data.rename(columns={'Symbol': StockPriceField.Symbol.value,
                                 'Open': StockPriceField.Open.value,
                                 'High': StockPriceField.High.value,
                                 'Low': StockPriceField.Low.value,
                                 'Close': StockPriceField.Close.value,
                                 'Volume': StockPriceField.Volume.value}, inplace=True)
        except Exception as e:
            self.logger.error("Failed to get (%s) price history from morningstar, %s", symbol, e)
        return data

    def _download_iex(self, symbol: str, start: datetime.datetime, end: datetime.datetime) -> pd.DataFrame:
        data = None
        try:
            earliest = datetime.datetime.today() - relativedelta(years=5)
            start = max(earliest, start)
            end = max(earliest, end)
            data = web.DataReader(symbol.strip(), 'iex', start, end, retry_count=self.retry)
            # data.reset_index(level=[0], inplace=True)
            data.index.rename(StockPriceField.Date.value, inplace=True)
            data[StockPriceField.Symbol.value] = symbol.strip()
            data.rename(columns={'open': StockPriceField.Open.value,
                                 'high': StockPriceField.High.value,
                                 'low': StockPriceField.Low.value,
                                 'close': StockPriceField.Close.value,
                                 'volume': StockPriceField.Volume.value}, inplace=True)
        except Exception as e:
            self.logger.error("Failed to get (%s) price history from iex, %s", symbol, e)
        return data

    def _download_quandl(self, symbol: str, start: datetime.datetime, end: datetime.datetime) -> pd.DataFrame:
        data = None
        try:
            data = web.DataReader('WIKI/%s' % symbol.strip(), 'quandl', start, end + datetime.timedelta(days=1),
                                  retry_count=self.retry)
            data = data[['AdjOpen', 'AdjHigh', 'AdjLow', 'AdjClose', 'AdjVolume']]
            data.index.rename(StockPriceField.Date.value, inplace=True)
            data[StockPriceField.Symbol.value] = symbol.strip()
            data.rename(columns={'AdjOpen': StockPriceField.Open.value,
                                 'AdjHigh': StockPriceField.High.value,
                                 'AdjLow': StockPriceField.Low.value,
                                 'AdjClose': StockPriceField.Close.value,
                                 'AdjVolume': StockPriceField.Volume.value}, inplace=True)
        except Exception as e:
            self.logger.error("Failed to get (%s) price history from quandl, %s", symbol, e)
        return data
