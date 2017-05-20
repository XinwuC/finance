import datetime
import logging.config
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP

from stock.china.china_market import ChinaMarket
from stock.us.strategy_executor import StrategyExecutor
from stock.us.us_market import UsaMarket
from utility.utility import Utility


def run_us_market():
    # refresh stock lists
    us_market = UsaMarket()
    us_market.refresh_listing()
    us_market.refresh_stocks()

    # run us stock strategies
    strategy_executor = StrategyExecutor()
    buying_options = strategy_executor.run()
    logging.info('%s strategies found opportunities.' % len(buying_options))
    if len(buying_options) > 0:
        # post-processing
        text_content = ''
        html_content = '<html><head /><body>'
        for name in buying_options:
            text_content += '%s\n\n%s\n\n' % (name, buying_options[name].to_string())
            html_content += '<h3>%s</h3><p>%s</p>' % (name, buying_options[name].to_html())
        html_content += '</body></html>'

        # write results to file
        file_path = Utility.get_data_folder(Utility.Market.US, Utility.DataFolder.Output)
        file_name = os.path.join(file_path, '%s.txt' % datetime.date.today())
        with open(file_name, 'w+') as file:
            file.write(text_content)

        # send mail
        msg = MIMEMultipart('alternative')
        msg['From'] = 'Xinwu <xwcheng@live.com>'
        msg['To'] = 'chengxinwu@yahoo.com'
        msg['Subject'] = 'Stocks'
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        with SMTP('smtp.live.com', '587') as smtp:
            smtp.starttls()
            smtp.login('xwcheng@live.com', '2011fortesting')
            smtp.sendmail(msg['From'], msg['To'], msg.as_string())
            logging.info('Send opportunities through mail to %s', msg['To'])


def run_china_market():
    market = ChinaMarket()
    market.refresh_listing()
    market.refresh_stocks()


if __name__ == '__main__':
    # init logging
    os.makedirs('logs', exist_ok=True)
    logging.config.dictConfig(Utility.get_logging_config())

    try:
        run_us_market()
        logging.info("US market is finished.")
    except BaseException as e:
        logging.exception(e)

    try:
        run_china_market()
        logging.info("China market is finished.")
    except BaseException as e:
        logging.exception(e)
