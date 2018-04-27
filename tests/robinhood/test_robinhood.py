import unittest
from unittest.mock import patch

from robinhood.robinhood import RobinhoodAccount


@patch('robinhood.robinhood.Robinhood')
class RobinhoodAccountTestCase(unittest.TestCase):
    def test_get_max_trade_price_bid(self, mock):
        target = RobinhoodAccount('', '')
        last_trade_price = 100
        bid_price = 200
        target.robinhood.last_trade_price.return_value = [[str(last_trade_price), '']]
        target.robinhood.bid_price.return_value = [[str(bid_price), '']]
        self.assertEqual(target.get_max_trade_price('symbol'), bid_price)
        self.assertTrue(target.robinhood.last_trade_price.called)
        self.assertTrue(target.robinhood.bid_price.called)
        self.assertFalse(target.robinhood.ask_price.called)

    def test_get_max_trade_price_last_trade(self, mock):
        target = RobinhoodAccount('', '')
        last_trade_price = 250
        bid_price = 200
        ask_price = 300
        target.robinhood.last_trade_price.return_value = [[str(last_trade_price), '']]
        target.robinhood.bid_price.return_value = [[str(bid_price), '']]
        target.robinhood.ask_price.return_value = [[str(ask_price), '']]
        self.assertEqual(target.get_max_trade_price('symbol'), last_trade_price)
        self.assertTrue(target.robinhood.last_trade_price.called)
        self.assertTrue(target.robinhood.bid_price.called)
        self.assertFalse(target.robinhood.ask_price.called)

    def test_get_max_trade_price_last_trade_2(self, mock):
        target = RobinhoodAccount('', '')
        last_trade_price = 100
        bid_price = 200
        ask_price = 300
        target.robinhood.last_trade_price.return_value = [[str(last_trade_price), '']]
        target.robinhood.bid_price.return_value = [[str(bid_price), '']]
        target.robinhood.ask_price.return_value = [[str(ask_price), '']]
        self.assertEqual(target.get_max_trade_price('symbol', bid_price=False, ask_price=False), last_trade_price)
        self.assertTrue(target.robinhood.last_trade_price.called)
        self.assertFalse(target.robinhood.bid_price.called)
        self.assertFalse(target.robinhood.ask_price.called)

    def test_get_max_trade_price_last_trade_3(self, mock):
        target = RobinhoodAccount('', '')
        last_trade_price = 400
        bid_price = 200
        ask_price = 300
        target.robinhood.last_trade_price.return_value = [[str(last_trade_price), '']]
        target.robinhood.bid_price.return_value = [[str(bid_price), '']]
        target.robinhood.ask_price.return_value = [[str(ask_price), '']]
        self.assertEqual(target.get_max_trade_price('symbol', bid_price=False, ask_price=True), last_trade_price)
        self.assertTrue(target.robinhood.last_trade_price.called)
        self.assertFalse(target.robinhood.bid_price.called)
        self.assertTrue(target.robinhood.ask_price.called)

    def test_get_max_trade_price_ask(self, mock):
        target = RobinhoodAccount('', '')
        last_trade_price = 250
        bid_price = 200
        ask_price = 300
        target.robinhood.last_trade_price.return_value = [[str(last_trade_price), '']]
        target.robinhood.bid_price.return_value = [[str(bid_price), '']]
        target.robinhood.ask_price.return_value = [[str(ask_price), '']]
        self.assertEqual(target.get_max_trade_price('symbol', ask_price=True), ask_price)
        self.assertTrue(target.robinhood.last_trade_price.called)
        self.assertTrue(target.robinhood.bid_price.called)
        self.assertTrue(target.robinhood.ask_price.called)

    def test_get_max_trade_price_ask_0(self, mock):
        target = RobinhoodAccount('', '')
        last_trade_price = 250
        bid_price = 200
        ask_price = 100
        target.robinhood.last_trade_price.return_value = [[str(last_trade_price), '']]
        target.robinhood.bid_price.return_value = [[str(bid_price), '']]
        target.robinhood.ask_price.return_value = [[str(ask_price), '']]
        self.assertEqual(target.get_max_trade_price('symbol', ask_price=True), last_trade_price)
        self.assertTrue(target.robinhood.last_trade_price.called)
        self.assertTrue(target.robinhood.bid_price.called)
        self.assertTrue(target.robinhood.ask_price.called)

    def test_get_max_trade_price_ask_1(self, mock):
        target = RobinhoodAccount('', '')
        last_trade_price = 250
        bid_price = 400
        ask_price = 300
        target.robinhood.last_trade_price.return_value = [[str(last_trade_price), '']]
        target.robinhood.bid_price.return_value = [[str(bid_price), '']]
        target.robinhood.ask_price.return_value = [[str(ask_price), '']]
        self.assertEqual(target.get_max_trade_price('symbol', bid_price=False, ask_price=True), ask_price)
        self.assertTrue(target.robinhood.last_trade_price.called)
        self.assertFalse(target.robinhood.bid_price.called)
        self.assertTrue(target.robinhood.ask_price.called)
