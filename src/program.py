import logging.config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP

from stock.china.china_market import ChinaMarket
from stock.us.us_market import UsaMarket
from utility.utility import *


def run_us_market():
    # refresh stock lists
    us_market = UsaMarket()
    us_market.refresh_listing()
    us_market.refresh_stocks()
    return us_market.run_strategies()


def run_china_market():
    market = ChinaMarket()
    market.refresh_listing()
    market.refresh_stocks()
    return market.run_strategies()


def record_buyings(buyings={}):
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
        file_name = os.path.join(file_path, '%s.txt' % datetime.date.today())
        with open(file_name, 'w+') as file:
            file.write(text_content)

        # send mail
        msg['Subject'] = 'Found stocks buying options'
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
    else:
        msg['Subject'] = 'No stocks buying options'

    with SMTP('smtp.live.com', '587') as smtp:
        smtp.starttls()
        smtp.login('xwcheng@live.com', '2011fortesting')
        smtp.sendmail(msg['From'], msg['To'], msg.as_string())
        logging.info('Send opportunities through mail to %s', msg['To'])


if __name__ == '__main__':
    # init logging
    os.makedirs('logs', exist_ok=True)
    logging.config.dictConfig(Utility.get_logging_config())

    buyings = {}
    try:
        buyings[Market.US] = run_us_market()
        logging.info(
            '%s strategies found opportunities for market %s.' % (len(buyings[Market.US]), Market.US.value))
    except BaseException as e:
        logging.exception(e)

    try:
        buyings[Market.China] = run_china_market()
        logging.info(
            '%s strategies found opportunities for market %s.' % (len(buyings[Market.China]), Market.China.value))
    except BaseException as e:
        logging.exception(e)

    try:
        record_buyings(buyings)
    except BaseException as e:
        logging.exception(e)
