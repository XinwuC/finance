#! /usr/bin/python

import argparse
import logging.config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP

import pandas
from dateutil import parser

from robinhood.robinhood import RobinhoodAccount
from robinhood.robinhood_utility import RobinhoodUtility
from stock.china_market import ChinaMarket
from stock.us_market import UsaMarket
from strategy.sell.sell_strategy_lock_profit import SimpleProfitLockSellStrategy
from utility.utility import *


class Program:
    def __init__(self):
        # init logging
        os.makedirs('logs', exist_ok=True)
        logging.config.dictConfig(Utility.get_logging_config())
        self.logger = logging.getLogger(__name__)
        self.config = Utility.get_config()

        self.args = self.parse_argument()
        self.us_market = UsaMarket(avkey=Utility.decrypt(self.args.avkey), qkey=Utility.decrypt(self.args.qkey))
        self.china_market = ChinaMarket()

    def generate_reports(self, buyings={}, sell_book: pandas.DataFrame = None) -> (str, str):
        text_report = ''
        html_report = '<html><head/><body>'
        # generate buyings report
        for market, buying_options in buyings.items():
            if len(buying_options) > 0:
                text_report += '===== %s =====\n\n' % market
                html_report += '<h1>%s</h1>' % market
                for name in buying_options:
                    text_report += '%s\n\n%s\n\n' % (name, buying_options[name].to_string())
                    html_report += '<h3>%s</h3><p>%s</p>' % (name, buying_options[name].to_html(escape=False,
                        formatters={'symbol': lambda x: Utility.get_stock_hyperlink(market, x)}))
        # generate sell book report
        if sell_book is not None:
            format_book = sell_book.reset_index()
            text_report += '===== Robinhood Account =====\n\n%s\n\n' % format_book.to_string()
            html_report += '<p><h1>Robinhood Account</h1><p>%s</p></p>' % format_book.to_html(escape=False,
                formatters={'index': lambda x: Utility.get_stock_hyperlink(Market.US, x)})
        # add html
        html_report += '</body></html>'
        return text_report, html_report

    def update_sell_book(self):
        sell_book = RobinhoodUtility.load_sell_book().astype('float')
        sell_book = pandas.concat([sell_book, pandas.DataFrame(columns=['cost_basis', 'shares', 'pre_low'])])
        # update sell book
        brokerage = RobinhoodAccount(self.config.robinhood_account, Utility.decrypt(self.args.rhp))
        sell_strategy = SimpleProfitLockSellStrategy()
        with brokerage:
            for position in brokerage.get_positions().values():
                # get position data
                symbol = position['symbol']
                shares = int(float(position['quantity']))
                cost_basis = float(position['average_buy_price'])
                # get sell order from sell book
                if symbol not in sell_book.index:
                    sell_book.loc[symbol] = {'low': 0.0, 'high': None, 'cost_basis': cost_basis, 'shares': shares,
                                             'pre_low': 0.0}
                else:
                    sell_book.loc[symbol, 'cost_basis'] = cost_basis
                    sell_book.loc[symbol, 'shares'] = shares
                    sell_book.loc[symbol, 'pre_low'] = sell_book['low'][symbol]
                # calculate new low target price
                history = self.us_market.refresh_stock(symbol=symbol, start=datetime.datetime(1990, 1, 1))
                new_sell_price = round(sell_strategy.get_sell_price(cost_basis, history), 2)
                # update sell order if conditions are met
                if new_sell_price > sell_book['low'][symbol]:
                    sell_book.loc[symbol, 'low'] = new_sell_price
        # upload sell book
        try:
            if RobinhoodUtility.upload_sell_book(sell_book[['low', 'high']], self.args.ght):
                self.logger.info("Uploaded new sell book to github.")
            else:
                self.logger.info("No change to sell book, skip upload.")
        except Exception as e:
            self.logger.exception('Failed to upload new sell book: %s', e)
        # return
        sell_book.loc[:, 'low_profit_%'] = sell_book['low'] / sell_book['cost_basis'] - 1
        sell_book.loc[:, 'low_profit_$$'] = (sell_book['low'] - sell_book['cost_basis']) * sell_book['shares']
        sell_book.loc[:, 'high_profit_%'] = sell_book['high'] / sell_book['cost_basis'] - 1
        sell_book.loc[:, 'high_profit_$$'] = (sell_book['high'] - sell_book['cost_basis']) * sell_book['shares']
        return sell_book

    def save_report(self, buyings, sell_book):
        text_report, html_report = self.generate_reports(buyings, sell_book)
        # save reports to file
        file_path = Utility.get_data_folder(DataFolder.Output)
        file_name = os.path.join(file_path, 'reports_%s' % datetime.date.today())
        with open('%s.txt' % file_name, 'w+') as file:
            file.write(text_report)
        with open('%s.html' % file_name, 'w+') as file:
            file.write(html_report)

        # send mail
        if self.args.send_mail:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.mail_account
            msg['To'] = self.config.mail_to
            msg['Subject'] = '[%s] Algorithm Trading Reports' % datetime.date.today()
            msg.attach(MIMEText(text_report, 'plain'))
            msg.attach(MIMEText(html_report, 'html'))

            # send mail
            with SMTP('smtp.live.com', '587') as smtp:
                smtp.starttls()
                smtp.login(self.config.mail_account, Utility.decrypt(self.args.mp))
                smtp.sendmail(msg['From'], msg['To'], msg.as_string())
                logging.info('Send opportunities through mail to %s', msg['To'])

        # log text report
        self.logger.info(text_report)

    def parse_argument(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--country', dest='country',
                            help='which country to run, currently only support us and china. skip to run both',
                            choices=[Market.US.value, Market.China.value, 'all'],
                            required=False, default='all', nargs='*')
        parser.add_argument('-m', '--mode', dest='mode',
                            help='''
                            which functions to run\n\n
                            listing - refresh stock listings\n
                            history - update price history for each listing\n
                            strategy - run all strategies to find buying options\n
                            robinhood - update orders for positions in Robinhood account''',
                            choices=['all', 'listing', 'history', 'strategy', 'robinhood'],
                            required=False, default='all', nargs='*')
        parser.add_argument('-s', '--stocks', dest='stocks', help='a stock list to run', required=False, nargs='*')
        parser.add_argument('-d', '--target_date', dest='target_date', help='target date to test', required=False)
        parser.add_argument('-mp', '--mail_password', dest='mp', default='', help='password to send the mail',
                            required=False)
        parser.add_argument('-rhp', '--robinhood_password', dest='rhp', default='', help='Robinhood account password',
                            required=False)
        parser.add_argument('-ght', '--github_token', dest='ght', default='', help='Github access token',
                            required=False)
        parser.add_argument('-avkey', '--alphavantage_key', dest='avkey', default='', help='AlphaVantage API key',
                            required=False)
        parser.add_argument('-qkey', '--quandl_key', dest='qkey', default='', help='Quandl API key',
                            required=False)
        parser.add_argument('--send_mail', dest='send_mail', help='send mail after run strategies', action='store_true')
        return parser.parse_args()

    def run(self):
        # add countries to run
        markets = []
        if 'all' in self.args.country or Market.US.value in self.args.country:
            markets.append(self.us_market)
        if 'all' in self.args.country or Market.China.value in self.args.country:
            markets.append(self.china_market)

        # execute functions as demanded
        buyings = {}
        for market in markets:
            if 'listing' in self.args.mode or 'all' in self.args.mode:
                try:
                    start = datetime.datetime.now()
                    market.refresh_listing()
                    end = datetime.datetime.now()
                    self.logger.info('Timing: refresh listing for market %s in %s second.', market.market,
                                     (end - start) // datetime.timedelta(seconds=1))
                except Exception as e:
                    self.logger.exception('Failed to refresh listing for %s' % market.market, e)
            if 'history' in self.args.mode or 'all' in self.args.mode:
                try:
                    start = datetime.datetime.now()
                    market.refresh_stocks(stock_list=self.args.stocks)
                    end = datetime.datetime.now()
                    self.logger.info('Timing: refresh price history for market %s in %s minutes.', market.market,
                                     (end - start) // datetime.timedelta(minutes=1))
                except Exception as e:
                    self.logger.exception('Failed to refresh price history for %s' % market.market, e)
            if 'strategy' in self.args.mode or 'all' in self.args.mode:
                try:
                    target_date = None
                    if self.args.target_date is not None:
                        target_date = parser.parse(self.args.target_date)
                    start = datetime.datetime.now()
                    buyings[market.market] = market.run_strategies(stock_list=self.args.stocks, target_date=target_date)
                    end = datetime.datetime.now()
                    self.logger.info('Timing: run strategies for market %s in %s second.', market.market,
                                     (end - start) // datetime.timedelta(seconds=1))
                    self.logger.info(
                        '%s strategies found opportunities for market %s.' % (
                            len(buyings[market.market]), market.market))
                except Exception as e:
                    self.logger.exception('Failed to run strategies for %s' % market.market, e)
        self.generate_reports(buyings)

        # refresh robinhood account
        sell_book = None
        if 'robinhood' in self.args.mode or 'all' in self.args.mode:
            try:
                self.logger.info('Update Robinhood sell book')
                sell_book = self.update_sell_book()
            except Exception as e:
                self.logger.exception('Failed to update Robinhood sell book', e)

        # record buying options if strategies have been evaluated
        self.save_report(buyings, sell_book)


if __name__ == '__main__':
    try:
        program = Program()
        with pandas.option_context('display.max_colwidth', -1):
            program.run()
    except Exception as e:
        logging.exception(e)
