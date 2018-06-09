import types
import unittest

from screeners.screener import *
from stock.stock import Stock
from utility.utility import *


class NameScreenerTestCases(unittest.TestCase):
    def setUp(self):
        self.config = types.SimpleNamespace()

    def test_None(self):
        self.config.excludes = 'Holding'
        target = NameScreener(self.config)
        self.assertTrue(target.screen(None))

    def test_name_screener(self):
        self.config.excludes = 'Holding|Holdings|Fund|Funds|ETF'
        target = NameScreener(self.config)
        self.assertFalse(target.screen(Stock('VGI', 'Virtus Global Multi-Sector Income Fund')))
        self.assertFalse(target.screen(Stock('EQH', 'AXA Equitable Holdings, Inc.')))
        self.assertFalse(target.screen(Stock('EUFN', 'iShares MSCI Europe Financials ETF')))

        self.assertTrue(target.screen(Stock('GOOG', 'Alphabet Inc.')))
        self.assertTrue(target.screen(Stock('GOOG')))
        self.assertTrue(target.screen(Stock('GOOG', '')))
        self.assertTrue(target.screen(Stock('GOOG', None)))


class PennyStockScreenerTestCases(unittest.TestCase):
    def setUp(self):
        self.test_data = pd.read_csv('tests/resources/us_stocks/DXCM.csv', index_col=0, parse_dates=True)

    def test_None(self):
        target = PennyStockScreener()
        self.assertTrue(target.screen(None))
        self.assertTrue(target.screen(Stock('')))

    def test_empty(self):
        stock = Stock('')
        stock.price = pd.DataFrame()
        self.assertTrue(PennyStockScreener().screen(stock))

    def test_penny(self):
        stock = Stock('')
        stock.price = self.test_data
        stock.price.loc[stock.price.index[-1], StockPriceField.Low.value] = 0.99
        self.assertFalse(PennyStockScreener().screen(stock))

    def test_not_penny(self):
        stock = Stock('')
        stock.price = self.test_data
        self.assertTrue(PennyStockScreener().screen(stock))
