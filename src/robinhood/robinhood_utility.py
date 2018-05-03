import datetime

import github
import pandas as pd
import pytz
from Robinhood import Robinhood


class RobinhoodUtility:
    __robinhood = Robinhood()
    __sell_book_path = 'configs/robinhood_sell_book.csv'

    @staticmethod
    def is_order_open(order: dict) -> bool:
        return order['state'] == 'queued' or order['state'] == 'unconfirmed' or order['state'] == 'confirmed'

    @staticmethod
    def instrument_2_symbol(instrument: str) -> str:
        return RobinhoodUtility.__robinhood.get_url(instrument)['symbol']

    @staticmethod
    def symbol_2_instrument(symbol: str) -> str:
        return RobinhoodUtility.__robinhood.get_url('https://api.robinhood.com/quotes/%s/' % symbol)['instrument']

    @staticmethod
    def is_market_open():
        current_time_est = datetime.datetime.now(pytz.timezone('US/Eastern'))
        return datetime.time(hour=9, minute=30) <= current_time_est.time() <= datetime.time(hour=16, minute=00)

    @staticmethod
    def get_max_trade_price(symbol: str, bid_price: bool = True, ask_price: bool = False) -> float:
        trade_prices = RobinhoodUtility.__robinhood.last_trade_price(symbol)
        if bid_price:
            trade_prices += RobinhoodUtility.__robinhood.bid_price(symbol)
        if ask_price:
            trade_prices += RobinhoodUtility.__robinhood.ask_price(symbol)
        return float(max(max(trade_prices)))

    @staticmethod
    def load_sell_book() -> pd.DataFrame:
        return pd.read_csv(RobinhoodUtility.__sell_book_path, index_col=0).astype('float')

    @staticmethod
    def save_sell_book(sell_book: pd.DataFrame):
        sell_book.to_csv(RobinhoodUtility.__sell_book_path)

    @staticmethod
    def upload_sell_book(sell_book: pd.DataFrame, github_token: str) -> bool:
        repo = github.Github(github_token).get_user().get_repo('finance')
        remote_path = '/%s' % RobinhoodUtility.__sell_book_path
        remote_file = repo.get_file_contents(remote_path)
        new_file = sell_book.to_csv()
        uploaded = False
        if remote_file.decoded_content != new_file.encode('ascii'):
            repo.update_file(remote_path, 'update sell book', sell_book.to_csv(), remote_file.sha)
            RobinhoodUtility.save_sell_book(sell_book)
            uploaded = True
        return uploaded
