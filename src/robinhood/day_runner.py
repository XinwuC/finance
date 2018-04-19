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
        sell_book = pd.read_csv('configs/robinhood_sell_book.csv', index_col=0).ix[:, 0].to_dict()
        positions = self.robinhood.get_positions()
        symbols = set(positions.keys()).intersection(sell_book.keys())
        if not symbols:
            self.logger.info('No positions to run, runbook: %d, positions: %d' % (len(sell_book), len(positions)))
            return

        while self.is_market_open():
            for symbol in symbols:
                try:
                    self.trade_target_price(positions[symbol], sell_book[symbol])
                except LoginFailed as e:
                    self.logger.error("failed to update sell order %d for %s: %s" % (sell_book[symbol], symbol, e))
                    self.robinhood.login()
                except Exception as e:
                    self.logger.error("failed to update sell order %d for %s: %s" % (sell_book[symbol], symbol, e))
            time.sleep(60)

    def is_market_open(self):
        current_time_est = datetime.datetime.now(pytz.timezone('US/Eastern'))
        return 9 <= current_time_est.hour < 20

    def trade_target_price(self, position, target_price: float):
        bid_prices = self.robinhood.bid_price(position['symbol'])
        max_bid, _ = max(bid_prices, key=lambda bids: bids[0])
        if float(max_bid) > target_price * 0.995:
            self.robinhood.cancel_all_orders(position['symbol'])
            self.robinhood.place_stop_limit_sell_order(position, target_price)


if __name__ == '__main__':
    day_runner = RobinhoodDayRunner()
    day_runner.run()
