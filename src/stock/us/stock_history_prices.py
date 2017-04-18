"""
Get stock history prices from Yahoo! Finance and Google Finance. Reconcile price info from Y! and Google if they 
does not match each other.
"""
import datetime
import glob
import logging
import os

import pandas
import pandas_datareader.data as web

from configs.configuration import Configuration


class StockHistoryPrices:
    def __init__(self):
        # get latest stock list file from local
        self.logger = logging.getLogger(__name__)
        self.configs = Configuration.get_us_config()
        self.history_folder = os.path.join(self.configs.data_path, self.configs.data_history_folder)
        os.makedirs(self.history_folder, exist_ok=True)

    def refresh(self):
        files = glob.glob(os.path.join(self.configs.data_path, self.configs.symbols_file + "*"))
        if not files:
            raise FileExistsError('Cannot find stock listing file %s in %s',
                                  self.configs.symbols_file,
                                  self.configs.data_path)

        total_symbols = 0
        symbols_no_data = 0
        yahoo_errors = 0
        google_errors = 0
        with pandas.ExcelFile(files[len(files) - 1]) as listings:
            for market in listings.sheet_names:
                self.logger.info('Fetching stock history prices from market %s.', market.upper())
                stocks = pandas.read_excel(listings, market)
                for stock in stocks.itertuples():
                    total_symbols += 1
                    (yahoo_error, google_error) = self.update_history_prices(market, stock)
                    yahoo_errors += yahoo_error
                    google_errors += google_error
                    symbols_no_data += (2 == yahoo_error + google_error)
        self.logger.error(
            'Stock prices update completed, %s (%s) symbols has no data, yahoo has %s errors and google has %s errors.',
            symbols_no_data, total_symbols, yahoo_errors, google_errors)

    def update_history_prices(self, market, stock):
        year = int(stock.IPOyear) if stock.IPOyear != 'n/a' else self.configs.default_first_history_year
        start = datetime.datetime(year, 1, 1)
        end = datetime.date.today()
        yahoo_data = self._get_yahoo_data(market, stock, start, end)
        google_data = self._get_google_data(market, stock, start, end)
        stock_prices = self._reconcile_data(yahoo_data, google_data)

        if stock_prices is not None:
            stock_prices_file = os.path.join(self.history_folder, '%s_%s.csv' % (market, stock.Symbol))
            stock_prices.to_csv(stock_prices_file)
            self.logger.info('Updated price history for [%s] %s (%s)\t[%s][%s] %s.', market.upper(),
                             stock.Symbol, stock.IPOyear, stock.Sector, stock.industry, stock.Name)

        return yahoo_data is None, google_data is None

    def _get_yahoo_data(self, market, stock, start, end):
        yahoo_data = None
        try:
            yahoo_data = web.get_data_yahoo(stock.Symbol, start, end)
        except Exception as e:
            self.logger.error("Failed to get Yahoo! data for [%s] %s - %s price history, %s", market.upper(),
                              stock.Symbol,
                              stock.Name, e)
        return yahoo_data

    def _get_google_data(self, market, stock, start, end):
        google_data = None
        try:
            google_data = web.get_data_google(stock.Symbol, start, end)
        except Exception as e:
            self.logger.error("Failed to get Google data for [%s] %s - %s price history, %s", market.upper(),
                              stock.Symbol,
                              stock.Name, e)
        return google_data

    def _reconcile_data(self, yahoo_data, google_data):
        if yahoo_data is None:
            return google_data
        if google_data is None:
            return yahoo_data
        # TODO: add reconcile logic here, for now simply use yahoo_data first
        return yahoo_data
