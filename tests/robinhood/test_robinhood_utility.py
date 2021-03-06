import datetime
import unittest
from unittest.mock import patch

from robinhood.robinhood_utility import RobinhoodUtility


class RobinhoodUtilityTestCase(unittest.TestCase):

    def test_is_order_open(self):
        order = {'state': 'queued'}
        self.assertTrue(RobinhoodUtility.is_order_open(order))
        order['state'] = 'unconfirmed'
        self.assertTrue(RobinhoodUtility.is_order_open(order))
        order['state'] = 'confirmed'
        self.assertTrue(RobinhoodUtility.is_order_open(order))
        order['state'] = 'partially_filled'
        self.assertFalse(RobinhoodUtility.is_order_open(order))
        order['state'] = 'filled'
        self.assertFalse(RobinhoodUtility.is_order_open(order))
        order['state'] = 'rejected'
        self.assertFalse(RobinhoodUtility.is_order_open(order))
        order['state'] = 'canceled'
        self.assertFalse(RobinhoodUtility.is_order_open(order))
        order['state'] = 'failed'

    def test_instrument_2_symbol(self):
        symbol = 'GOOG'
        instrument = RobinhoodUtility.symbol_2_instrument(symbol)
        self.assertEqual(symbol, RobinhoodUtility.instrument_2_symbol(instrument))

    @patch('robinhood.robinhood_utility.datetime.datetime')
    def test_is_market_open(self, mock):
        mock = datetime.datetime.now()
        mock.time.return_value = datetime.time(hour=9, minute=29)
        self.assertFalse(RobinhoodUtility.is_market_open())
        mock.time.return_value = datetime.time(hour=9, minute=30)
        self.assertTrue(RobinhoodUtility.is_market_open())
        mock.time.return_value = datetime.time(hour=16, minute=00)
        self.assertTrue(RobinhoodUtility.is_market_open())
        mock.time.return_value = datetime.time(hour=16, minute=1)
        self.assertFalse(RobinhoodUtility.is_market_open())

    @patch('robinhood.robinhood_utility.Robinhood.last_trade_price', return_value=[['100', '']])
    @patch('robinhood.robinhood_utility.Robinhood.bid_price', return_value=[['200', '']])
    @patch('robinhood.robinhood_utility.Robinhood.ask_price', return_value=[['300', '']])
    def test_get_max_trade_price(self, *mocks):
        self.assertEqual(200, RobinhoodUtility.get_max_trade_price('GOOG'))
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.last_trade_price.called)
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.bid_price.called)
        self.assertFalse(RobinhoodUtility._RobinhoodUtility__robinhood.ask_price.called)

    @patch('robinhood.robinhood_utility.Robinhood.last_trade_price', return_value=[['250', '']])
    @patch('robinhood.robinhood_utility.Robinhood.bid_price', return_value=[['200', '']])
    @patch('robinhood.robinhood_utility.Robinhood.ask_price', return_value=[['300', '']])
    def test_get_max_trade_price_last_trade(self, *mocks):
        self.assertEqual(250, RobinhoodUtility.get_max_trade_price('GOOG'))
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.last_trade_price.called)
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.bid_price.called)
        self.assertFalse(RobinhoodUtility._RobinhoodUtility__robinhood.ask_price.called)

    @patch('robinhood.robinhood_utility.Robinhood.last_trade_price', return_value=[['100', '']])
    @patch('robinhood.robinhood_utility.Robinhood.bid_price', return_value=[['200', '']])
    @patch('robinhood.robinhood_utility.Robinhood.ask_price', return_value=[['300', '']])
    def test_get_max_trade_price_last_trade_2(self, *mocks):
        self.assertEqual(100, RobinhoodUtility.get_max_trade_price('GOOG', bid_price=False, ask_price=False))
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.last_trade_price.called)
        self.assertFalse(RobinhoodUtility._RobinhoodUtility__robinhood.bid_price.called)
        self.assertFalse(RobinhoodUtility._RobinhoodUtility__robinhood.ask_price.called)

    @patch('robinhood.robinhood_utility.Robinhood.last_trade_price', return_value=[['400', '']])
    @patch('robinhood.robinhood_utility.Robinhood.bid_price', return_value=[['200', '']])
    @patch('robinhood.robinhood_utility.Robinhood.ask_price', return_value=[['300', '']])
    def test_get_max_trade_price_last_trade_3(self, *mocks):
        self.assertEqual(400, RobinhoodUtility.get_max_trade_price('GOOG', bid_price=False, ask_price=True))
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.last_trade_price.called)
        self.assertFalse(RobinhoodUtility._RobinhoodUtility__robinhood.bid_price.called)
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.ask_price.called)

    @patch('robinhood.robinhood_utility.Robinhood.last_trade_price', return_value=[['250', '']])
    @patch('robinhood.robinhood_utility.Robinhood.bid_price', return_value=[['200', '']])
    @patch('robinhood.robinhood_utility.Robinhood.ask_price', return_value=[['300', '']])
    def test_get_max_trade_price_ask(self, *mocks):
        self.assertEqual(300, RobinhoodUtility.get_max_trade_price('GOOG', ask_price=True))
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.last_trade_price.called)
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.bid_price.called)
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.ask_price.called)

    @patch('robinhood.robinhood_utility.Robinhood.last_trade_price', return_value=[['250', '']])
    @patch('robinhood.robinhood_utility.Robinhood.bid_price', return_value=[['200', '']])
    @patch('robinhood.robinhood_utility.Robinhood.ask_price', return_value=[['100', '']])
    def test_get_max_trade_price_ask_0(self, *mocks):
        self.assertEqual(250, RobinhoodUtility.get_max_trade_price('GOOG', ask_price=True))
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.last_trade_price.called)
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.bid_price.called)
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.ask_price.called)

    @patch('robinhood.robinhood_utility.Robinhood.last_trade_price', return_value=[['250', '']])
    @patch('robinhood.robinhood_utility.Robinhood.bid_price', return_value=[['400', '']])
    @patch('robinhood.robinhood_utility.Robinhood.ask_price', return_value=[['300', '']])
    def test_get_max_trade_price_ask_1(self, *mocks):
        self.assertEqual(300, RobinhoodUtility.get_max_trade_price('GOOG', bid_price=False, ask_price=True))
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.last_trade_price.called)
        self.assertFalse(RobinhoodUtility._RobinhoodUtility__robinhood.bid_price.called)
        self.assertTrue(RobinhoodUtility._RobinhoodUtility__robinhood.ask_price.called)
