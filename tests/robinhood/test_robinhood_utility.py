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
