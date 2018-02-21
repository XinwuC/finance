#! /usr/bin/python

import argparse
import logging.config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP

import pandas
from dateutil import parser

from stock.china_market import ChinaMarket
from stock.us_market import UsaMarket
from utility.utility import *
from robinhood.profit_lock_seller import ProfitLockSeller
from robinhood.exceptions import RobinhoodException


class Program:
    def __init__(self):
        # init logging
        os.makedirs('logs', exist_ok=True)
        logging.config.dictConfig(Utility.get_logging_config())
        self.logger = logging.getLogger(__name__)
        self.config = Utility.get_config()

        self.args = self.parse_argument()
        self.text_report = ''
        self.html_report = ''

    def generate_buying_report(self, buyings={}):
        for market, buying_options in buyings.items():
            if len(buying_options) > 0:
                self.text_report += '===== %s =====\n\n' % market
                self.html_report += '<h1>%s</h1>' % market
                for name in buying_options:
                    self.text_report += '%s\n\n%s\n\n' % (name, buying_options[name].to_string())
                    self.html_report += '<h3>%s</h3><p>%s</p>' % (
                        name,
                        buying_options[name].to_html(escape=False,
                                                     formatters={
                                                         'symbol': lambda x:
                                                         '<a href="{0}/{1}">{1}</a>'.format(
                                                             Utility.get_config(Market(market)).symbol_page,
                                                             x)}
                                                     ))

    def refresh_robinhood_account(self):
        # refresh Robinhood and update orders
        robinhood = ProfitLockSeller()
        robinhood.login(username=self.config.robinhood_account, password=Utility.decrypt(self.args.rhp))
        self.logger.info('Login Robinhood successfully: %s' % self.config.robinhood_account)
        robinhood.refresh_account()
        for symbol, position in robinhood.positions.items():
            try:
                robinhood.update_sell_order(symbol)
            except RobinhoodException as e:
                self.logger.exception("Error when update sell order for %s: %s", symbol, e)

        # generate reports
        self.text_report += '===== Robinhood Account =====\n\n'
        self.text_report += '\n'.join(robinhood.reports)
        self.html_report += '<p><h1>Robinhood Account</h1><ul><li>%s</li></ul></p>' % (
            '</li><li>'.join(robinhood.reports))

    def save_report(self):
        # add html head
        self.html_report = '<html><head /><body>%s</body></html>' % self.html_report
        # save reports to file
        file_path = Utility.get_data_folder(DataFolder.Output)
        file_name = os.path.join(file_path, 'reports_%s' % datetime.date.today())
        with open('%s.txt' % file_name, 'w+') as file:
            file.write(self.text_report)
        with open('%s.html' % file_name, 'w+') as file:
            file.write(self.html_report)

        # send mail
        if self.args.send_mail:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.mail_account
            msg['To'] = self.config.mail_to
            msg['Subject'] = '[%s] Algorithm Trading Reports' % datetime.date.today()
            msg.attach(MIMEText(self.text_report, 'plain'))
            msg.attach(MIMEText(self.html_report, 'html'))

            # send mail
            with SMTP('smtp.live.com', '587') as smtp:
                smtp.starttls()
                smtp.login(self.config.mail_account, Utility.decrypt(self.args.mp))
                smtp.sendmail(msg['From'], msg['To'], msg.as_string())
                logging.info('Send opportunities through mail to %s', msg['To'])

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
        parser.add_argument('-avkey', '--alphavantage_key', dest='avkey', default='', help='AlphaVantage API key',
                            required=False)
        parser.add_argument('-qkey', '--quandl_key', dest='qkey', default='', help='Quandl API key',
                            required=False)
        parser.add_argument('--send_mail', dest='send_mail', help='send mail after run strategies', action='store_true')
        return parser.parse_args()

    def run(self):
        # add countries to run
        markets = []
        if 'all' in self.args.country:
            markets.append(UsaMarket(avkey=Utility.decrypt(self.args.avkey), qkey=Utility.decrypt(self.args.qkey)))
            markets.append(ChinaMarket())
        else:
            for c in self.args.country:
                if Market.US.value == c:
                    markets.append(UsaMarket(avkey=Utility.decrypt(self.args.avkey),
                                             qkey=Utility.decrypt(self.args.qkey)))
                elif Market.China.value == c:
                    markets.append(ChinaMarket())

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
        self.generate_buying_report(buyings)

        # refresh robinhood account
        if 'robinhood' in self.args.mode or 'all' in self.args.mode:
            try:
                self.logger.info('refresh Robinhood account')
                self.refresh_robinhood_account()
            except Exception as e:
                self.logger.exception('Failed to refresh Robinhood account', e)

        # record buying options if strategies have been evaluated
        self.save_report()


if __name__ == '__main__':
    try:
        program = Program()
        with pandas.option_context('display.max_colwidth', -1):
            program.run()
    except Exception as e:
        logging.exception(e)
