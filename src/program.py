import datetime
import logging.config
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from configs.configuration import Configuration
from stock.us.stock_history_prices import StockHistoryPrices
from stock.us.stock_listings import StockListings
from stock.us.strategy_executor import StrategyExecutor

if __name__ == '__main__':
    # init logging
    os.makedirs('logs', exist_ok=True)
    logging.config.dictConfig(Configuration.get_logging_config())
    configs = Configuration.get_us_config()

    # refresh stock lists
    stock_listings = StockListings()
    stock_listings.refresh()

    # refresh stock prices
    stock_history_prices = StockHistoryPrices()
    stock_history_prices.refresh()

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
        file_path = os.path.join(configs.data_path, configs.data_output_folder)
        os.makedirs(file_path, exist_ok=True)
        file_name = os.path.join(file_path, '%s.txt' % datetime.date.today())
        with open(file_name, 'w+') as file:
            file.write(text_content)

        # send mail
        msg = MIMEMultipart('alternative')
        msg["From"] = "xwcheng@msn.com"
        msg["To"] = "chengxinwu@yahoo.com"
        msg["Subject"] = "Stocks"
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        p = os.popen("/usr/sbin/sendmail -t -oi", 'w')
        p.write(msg.as_string())
