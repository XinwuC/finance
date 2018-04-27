import os
import unittest

from stock.us_market import UsaMarket
from utility.utility import Utility, Market


class UsaMarketTestCases(unittest.TestCase):

    def setUp(self):
        self.listing_file = Utility.get_stock_listing_xlsx(Market.US)
        self.stock_file_CINF = Utility.get_stock_price_history_file(Market.US, 'CINF')
        self.stock_file_GOOG = Utility.get_stock_price_history_file(Market.US, 'GOOG')
        self.stock_file_MMM = Utility.get_stock_price_history_file(Market.US, 'MMM')
        self.stock_file_GS = Utility.get_stock_price_history_file(Market.US, 'GS')

    def test_refresh_listing(self):
        target = UsaMarket()

        target.refresh_listing()
        self.assertTrue(os.path.exists(self.listing_file))
        self.assertGreater(os.stat(self.listing_file).st_size, 0, 'stock listing file %s size is 0' % self.listing_file)

    def test_refresh_stock(self):
        target = UsaMarket()

        target.refresh_stocks(stock_list=['CINF', 'GOOG', 'MMM', 'GS'])
        self.assertTrue(os.path.exists(self.stock_file_CINF))
        self.assertTrue(os.path.exists(self.stock_file_GOOG))
        self.assertTrue(os.path.exists(self.stock_file_MMM))
        self.assertTrue(os.path.exists(self.stock_file_GS))

        self.assertGreater(os.stat(self.stock_file_CINF).st_size, 0, 'size is 0: %s' % self.stock_file_CINF)
        self.assertGreater(os.stat(self.stock_file_GOOG).st_size, 0, 'size is 0: %s' % self.stock_file_GOOG)
        self.assertGreater(os.stat(self.stock_file_MMM).st_size, 0, 'size is 0: %s' % self.stock_file_MMM)
        self.assertGreater(os.stat(self.stock_file_GS).st_size, 0, 'size is 0: %s' % self.stock_file_GS)
