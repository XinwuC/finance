import unittest

import pandas

from strategy.sell.sell_strategy_lock_profit import SimpleProfitLockSellStrategy
from utility.utility import *


class SimpleProfitLockSellStrategyTestCase(unittest.TestCase):
    def setUp(self):
        self.test_data = pandas.read_csv('tests/resources/us_stocks/DXCM.csv', index_col=0, parse_dates=True)

    def test_get_sell_price(self):
        target = SimpleProfitLockSellStrategy()
        sell_price = target.get_sell_price(self.test_data)
        self.assertAlmostEqual(sell_price, 49.05, 2)
        self.assertTrue(sell_price > 0, msg='sell_price returned is <=0')
        self.assertTrue(sell_price < self.test_data[StockPriceField.Low.value][-1],
                        'sell_price is higher than current market price.')

    def test_get_sell_price_w_target_date(self):
        target = SimpleProfitLockSellStrategy()
        target_date = datetime.date(2017, 11, 1)
        sell_price = target.get_sell_price(self.test_data, target_date)
        self.assertAlmostEqual(sell_price, 42.40, 2)
        self.assertTrue(sell_price > 0, msg='sell_price returned is <=0')
        self.assertTrue(sell_price < self.test_data[StockPriceField.Low.value][target_date],
                        'sell_price is higher than current market price.')
