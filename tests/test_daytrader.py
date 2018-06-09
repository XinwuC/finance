import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from daytrader import RobinhoodIntraDayTrader
from robinhood.robinhood_utility import RobinhoodUtility


@patch('daytrader.argparse.ArgumentParser')
@patch('daytrader.RobinhoodAccount')
class RobinhoodDayTraderTestCase(unittest.TestCase):

    def test_trade_target_price_reverse(self, *mocks):
        self.verify_combination(cost=0, low=200, high=100, bid=0, traded=False)

    def test_trade_target_price_equal_high_low_0(self, *mocks):
        self.verify_combination(cost=199.99, low=200, high=200, bid=199.99, traded=True, target_price=200)

    def test_trade_target_price_equal_high_low_1(self, *mocks):
        self.verify_combination(cost=200, low=200, high=200, bid=199.99, traded=True, target_price=200)

    def test_trade_target_price_equal_high_low_2(self, *mocks):
        self.verify_combination(cost=200.01, low=200, high=200, bid=199.99, traded=False)

    def test_trade_target_price_low_0(self, *mocks):
        self.verify_combination(cost=99.99, low=100, high=200, bid=100.01, traded=True, target_price=100)

    def test_trade_target_price_low_1(self, *mocks):
        self.verify_combination(cost=100, low=100, high=200, bid=100.01, traded=True, target_price=100)

    def test_trade_target_price_low_2(self, *mocks):
        self.verify_combination(cost=100.01, low=100, high=200, bid=100.01, traded=False)

    def test_trade_target_price_low_3(self, *mocks):
        self.verify_combination(cost=90, low=100, high=200, bid=99.99, traded=False)

    def test_trade_target_price_high_0(self, *mocks):
        self.verify_combination(cost=199.99, low=100, high=200, bid=199.99, traded=True, target_price=200)

    def test_trade_target_price_high_1(self, *mocks):
        self.verify_combination(cost=200, low=100, high=200, bid=199.99, traded=True, target_price=200)

    def test_trade_target_price_high_2(self, *mocks):
        self.verify_combination(cost=200.01, low=100, high=200, bid=199.99, traded=False)

    def test_trade_target_price_high_3(self, *mocks):
        self.verify_combination(cost=10, low=100, high=200, bid=400, traded=True, target_price=400)

    def verify_combination(self, cost, low, high, bid, traded, target_price=0):
        RobinhoodUtility.get_max_trade_price = MagicMock(return_value=bid)
        target = RobinhoodIntraDayTrader()
        target.trade_target_price({'symbol': 'GOOG', 'average_buy_price': cost, 'quantity': 100}, low, high)
        self.assertEqual(traded, target.robinhood.place_stop_limit_sell_order.called)
        if traded:
            self.assertEqual(target_price, target.robinhood.place_stop_limit_sell_order.call_args[0][1])
        return target

    def test_place_stop_limit_sell_order_0(self, *mocks):
        target = RobinhoodIntraDayTrader()
        target.robinhood.get_open_orders.return_value = []
        target.place_stop_limit_sell_order({'symbol': 'GOOG', 'average_buy_price': 1000, 'quantity': 100}, 1234)
        self.assertFalse(target.robinhood.cancel_order.called)
        self.assertTrue(target.robinhood.place_stop_limit_sell_order.called)
        self.assertEqual(1234, target.robinhood.place_stop_limit_sell_order.call_args[0][1])

    def test_place_stop_limit_sell_order_1(self, *mocks):
        target = RobinhoodIntraDayTrader()
        target.robinhood.get_open_orders.return_value = [{'side':'sell', 'price': '1000'}]
        target.place_stop_limit_sell_order({'symbol': 'GOOG', 'average_buy_price': 1000, 'quantity': 100}, 1234)
        self.assertTrue(target.robinhood.cancel_order.called)
        self.assertTrue(target.robinhood.place_stop_limit_sell_order.called)
        self.assertEqual(1234, target.robinhood.place_stop_limit_sell_order.call_args[0][1])

    def test_place_stop_limit_sell_order_2(self, *mocks):
        target = RobinhoodIntraDayTrader()
        target.robinhood.get_open_orders.return_value = [{'side':'sell', 'price': '2000'}]
        target.place_stop_limit_sell_order({'symbol': 'GOOG', 'average_buy_price': 1000, 'quantity': 100}, 1234)
        self.assertFalse(target.robinhood.cancel_order.called)
        self.assertFalse(target.robinhood.place_stop_limit_sell_order.called)

    def test_place_stop_limit_sell_order_3(self, *mocks):
        target = RobinhoodIntraDayTrader()
        target.robinhood.get_open_orders.return_value = [{'side':'sell', 'price': '1001'}]
        target.place_stop_limit_sell_order({'symbol': 'GOOG', 'average_buy_price': 1000, 'quantity': 100}, 1234, True)
        self.assertTrue(target.robinhood.cancel_order.called)
        self.assertTrue(target.robinhood.place_stop_limit_sell_order.called)
        self.assertEqual(1234, target.robinhood.place_stop_limit_sell_order.call_args[0][1])
