#! /usr/local/bin/python3

import argparse
import logging.config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP

from stock.china.china_market import ChinaMarket
from stock.us.us_market import UsaMarket
from utility.utility import *


def record_buyings(buyings={}, send_mail=True):
    text_content = ''
    html_content = '<html><head /><body>'
    count = 0
    for market, buying_options in buyings.items():
        if len(buying_options) > 0:
            text_content += '===== %s =====\n\n' % market
            html_content += '<h1>%s</h1>' % market
            for name in buying_options:
                count += 1
                text_content += '%s\n\n%s\n\n' % (name, buying_options[name].to_string())
                html_content += '<h3>%s</h3><p>%s</p>' % (name, buying_options[name].to_html())
    html_content += '</body></html>'

    msg = MIMEMultipart('alternative')
    msg['From'] = 'Xinwu <xwcheng@live.com>'
    msg['To'] = 'chengxinwu@yahoo.com'
    if count > 0:
        # write results to file
        file_path = Utility.get_data_folder(Market.US, DataFolder.Output)
        file_name = os.path.join(file_path, '%s.txt' % datetime.datetime.today())
        with open(file_name, 'w+') as file:
            file.write(text_content)

        # send mail
        msg['Subject'] = 'Found stocks buying options'
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
    else:
        msg['Subject'] = 'No stocks buying options'

    if send_mail:
        with SMTP('smtp.live.com', '587') as smtp:
            smtp.starttls()
            smtp.login('xwcheng@live.com', '2011fortesting')
            smtp.sendmail(msg['From'], msg['To'], msg.as_string())
            logging.info('Send opportunities through mail to %s', msg['To'])


def parse_argument():
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
                        strategy - run all strategies to find buying options''',
                        choices=['all', 'listing', 'history', 'strategy'],
                        required=False, default='all', nargs='*')
    parser.add_argument('-s', '--stocks', dest='stocks', help='a stock list to run', required=False, nargs='*')
    parser.add_argument('--send_mail', dest='send_mail', help='send mail after run strategies', action='store_true')
    return parser.parse_args()


def run(args):
    # add countries to run
    markets = []
    if 'all' in args.country:
        markets.append(UsaMarket())
        markets.append(ChinaMarket())
    else:
        for c in args.country:
            if Market.US.value == c:
                markets.append(UsaMarket())
            elif Market.China.value == c:
                markets.append(ChinaMarket())

    # execute functions as demanded
    buyings = {}
    for market in markets:
        if 'listing' in args.mode or 'all' in args.mode:
            try:
                market.refresh_listing()
            except Exception as e:
                logging.exception('Failed to refresh listing for %s' % market.market, e)
        if 'history' in args.mode or 'all' in args.mode:
            try:
                market.refresh_stocks(stock_list=args.stocks)
            except Exception as e:
                logging.exception('Failed to refresh price history for %s' % market.market, e)
        if 'strategy' in args.mode or 'all' in args.mode:
            try:
                buyings[market.market] = market.run_strategies(stock_list=args.stocks)
                logging.info(
                    '%s strategies found opportunities for market %s.' % (len(buyings[market.market]), market.market))
            except Exception as e:
                logging.exception('Failed to run strategies for %s' % market.market, e)

    # record buying options if strategies have been evaluated
    if 'strategy' in args.mode or 'all' in args.mode:
        record_buyings(buyings, args.send_mail)


if __name__ == '__main__':
    # init logging
    os.makedirs('logs', exist_ok=True)
    logging.config.dictConfig(Utility.get_logging_config())

    try:
        run(parse_argument())
    except Exception as e:
        logging.exception(e)
