import argparse
import datetime
import logging.config
import os
import time

import pandas as pd
import pytz
from Robinhood.exceptions import LoginFailed

from robinhood import RobinhoodAccount
from utility.utility import Utility


class RobinhoodDayRunner:
    def __init__(self):
        # init logging
        os.makedirs('logs', exist_ok=True)
        logging.config.dictConfig(Utility.get_logging_config())
        self.logger = logging.getLogger(__name__)
        self.config = Utility.get_config()

        self.args = self.parse_argument()
        self.robinhood = RobinhoodAccount(self.config.robinhood_account, Utility.decrypt(self.args.rhp))
        self.logger.info('Login robinhood successful.')

    def parse_argument(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-rhp', '--robinhood_password', dest='rhp', default='', help='Robinhood account password',
                            required=True)
        parser.add_argument('-mp', '--mail_password', dest='mp', default='', help='password to send the mail',
                            required=False)
        parser.add_argument('--send_mail', dest='send_mail', help='send mail after run strategies', action='store_true')
        return parser.parse_args()

    def run(self):
        sell_book = pd.read_csv('configs/robinhood_sell_book.csv', index_col=0)
        positions = self.robinhood.get_positions()
        symbols = set(positions.keys()).intersection(sell_book.index)
        if not symbols:
            self.logger.info('No positions to run, sell book: %d, positions: %d' % (sell_book.shape[0], len(positions)))
            return

        self.logger.info('Start to track live market price and follow sell book to sell.')
        while self.is_market_open():
            for symbol in symbols:
                try:
                    self.trade_target_price(positions[symbol], sell_book['low'][symbol], sell_book['high'][symbol])
                except LoginFailed as e:
                    self.logger.error("failed to update sell order %d for %s: %s" % (sell_book[symbol], symbol, e))
                    self.robinhood.login()
                except Exception as e:
                    self.logger.error("failed to update sell order %d for %s: %s" % (sell_book[symbol], symbol, e))
            time.sleep(60)
        self.logger.info('Market closed.')

    def is_market_open(self):
        current_time_est = datetime.datetime.now(pytz.timezone('US/Eastern'))
        return 9 <= current_time_est.hour < 16

    def trade_target_price(self, position, low_target: float, high_target: float):
        max_trade_price = self.robinhood.get_max_trade_price(position['symbol'])
        cost_basis = float(position['average_buy_price'])
        shares = int(float(position['quantity']))

        self.logger.info(
            'Checking {0}, cost: ${1:.2f}, target: [${2:.2f}, ${3:.2f}], '.format(position['symbol'], cost_basis,
                                                                                  low_target, high_target) +
            'current bid: ${0:.2f} ({1:.2%}, ${2:.2f})'.format(max_trade_price, max_trade_price / cost_basis - 1,
                                                               (max_trade_price - cost_basis) * shares))
        if max_trade_price > high_target * 0.9995:
            # place high target sell order
            self.robinhood.cancel_all_orders(position['symbol'])
            self.robinhood.place_stop_limit_sell_order(position, high_target)
            self.logger.info('New sell order placed for {0} @ ${1:.2f} ({2:+.2%}, ${3:+.2f})'.format(
                position['symbol'], high_target, high_target / cost_basis - 1, (high_target - cost_basis) * shares))
        elif max_trade_price < low_target * 1.01:
            # place low target sell order
            self.robinhood.cancel_all_orders(position['symbol'])
            self.robinhood.place_stop_limit_sell_order(position, low_target)
            self.logger.info('New sell order placed for {0} @ ${1:.2f} ({2:+.2%}, ${3:+.2f})'.format(
                position['symbol'], low_target, low_target / cost_basis - 1, (high_target - cost_basis) * shares))


if __name__ == '__main__':
    day_runner = RobinhoodDayRunner()
    day_runner.run()
