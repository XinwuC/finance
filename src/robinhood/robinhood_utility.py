import datetime

import pytz
from Robinhood import Robinhood


class RobinhoodUtility:
    __robinhood = Robinhood()

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
