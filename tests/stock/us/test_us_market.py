import unittest
import os
from stock.us.us_market import UsaMarket

from utility.utility import *


class UsaMarketTestCases(unittest.TestCase):
    def test_refresh_listing(self):
        target = UsaMarket()
        target.refresh_listing()

        listing_file = Utility.get_stock_listing_xlsx(Market.US)
        self.assertTrue(os.path.exists(listing_file))
