import argparse
import logging.config
import os
import time

import pandas as pd
from Robinhood.exceptions import LoginFailed

from robinhood.robinhood import RobinhoodAccount
from robinhood.robinhood_utility import RobinhoodUtility
from utility.utility import Utility


class RobinhoodIntraDayTrader:
    def __init__(self):
        # init logging
        os.makedirs('logs', exist_ok=True)
        logging.config.dictConfig(Utility.get_logging_config())
        self.logger = logging.getLogger(__name__)
        self.config = Utility.get_config()

        self.args = self.parse_argument()
        self.robinhood = RobinhoodAccount(self.config.robinhood_account, Utility.decrypt(self.args.rhp))

    def parse_argument(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-rhp', '--robinhood_password', dest='rhp', default='', help='Robinhood account password',
                            required=True)
        return parser.parse_args()

    def run(self):
        sell_book = pd.read_csv('configs/robinhood_sell_book.csv', index_col=0)
        with self.robinhood:
            self.logger.info('Login Robinhood successful.')
            self.logger.info('Start to track live market price and follow sell book to sell.')
            while RobinhoodUtility.is_market_open():
                try:
                    positions = self.robinhood.get_positions()
                    symbols = set(positions.keys()).intersection(sell_book.index)
                    self.logger.info('%d stocks to run, sell book: %d, positions: %d' % (
                        len(symbols), sell_book.shape[0], len(positions)))
                    for symbol in symbols:
                        self.trade_target_price(positions[symbol], sell_book['low'][symbol], sell_book['high'][symbol])
                except LoginFailed as e:
                    self.logger.error("logged out, re-login again: %s" % e)
                    self.robinhood.login()
                except Exception as e:
                    self.logger.error("error when play sell book: %s" % e)
                finally:
                    time.sleep(60)
            self.logger.info('Market closed.')
        self.logger.info('Logout from Robinhood.')

    def trade_target_price(self, position, low_target: float, high_target: float):
        if low_target > high_target:
            self.logger.warning('({0}) low target price ${1:.2f} above high target ${2:.2f}, skip until fix.'.format(
                position['symbol'], low_target, high_target))
            return

        max_trade_price = RobinhoodUtility.get_max_trade_price(position['symbol'])
        cost_basis = float(position['average_buy_price'])
        shares = int(float(position['quantity']))

        self.logger.info(
            'Checking ({0}), cost: ${1:.2f}, target: [${2:.2f}, ${3:.2f}], '.format(position['symbol'], cost_basis,
                                                                                    low_target, high_target) +
            'current bid: ${0:.2f} ({1:.2%}, ${2:.2f})'.format(max_trade_price, max_trade_price / cost_basis - 1,
                                                               (max_trade_price - cost_basis) * shares))
        if max_trade_price > high_target * 0.995 and high_target >= cost_basis:
            # place high target sell order
            max_bid = RobinhoodUtility.get_max_trade_price(position['symbol'], bid_price=True, ask_price=True)
            high_target = max(high_target, max_bid)
            self.robinhood.cancel_all_orders(position['symbol'])
            self.robinhood.place_stop_limit_sell_order(position, high_target)
            self.logger.info('New sell order placed for {0} @ ${1:.2f} ({2:+.2%}, ${3:+.2f})'.format(
                position['symbol'], high_target, high_target / cost_basis - 1, (high_target - cost_basis) * shares))
        elif cost_basis <= low_target < max_trade_price < low_target * 1.01:
            # place low target sell order
            self.robinhood.cancel_all_orders(position['symbol'])
            self.robinhood.place_stop_limit_sell_order(position, low_target)
            self.logger.info('New sell order placed for {0} @ ${1:.2f} ({2:+.2%}, ${3:+.2f})'.format(
                position['symbol'], low_target, low_target / cost_basis - 1, (high_target - cost_basis) * shares))


if __name__ == '__main__':
    try:
        day_runner = RobinhoodIntraDayTrader()
        day_runner.run()
    except BaseException as e:
        logging.exception(e)
