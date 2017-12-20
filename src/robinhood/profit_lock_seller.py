import datetime
import logging
import os

from robinhood.Robinhood import Robinhood
from stock.us.us_market import UsaMarket
from strategy.sell.sell_strategy_lock_profit import SimpleProfitLockSellStrategy
from utility.utility import Utility


class ProfitLockSeller:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.market = UsaMarket()
        self.sell_strategy = SimpleProfitLockSellStrategy()
        self.robinhood = Robinhood()

        self.reports = []

    def login(self, username, password):
        return self.robinhood.login(username, password)

    def refresh_account(self):
        # get positions
        self.positions = {}
        for pos in self.robinhood.securities_owned()['results']:
            symbol = self._get_symbol_name(pos['instrument'])
            self.positions[symbol] = pos
            self.logger.info('Position: [%s] %s shares @ $%s' % (symbol, pos['quantity'], pos['average_buy_price']))
        # get open orders first
        self.open_orders = {}
        for order in self.robinhood.order_history()['results']:
            if self._is_order_open(order):
                symbol = self._get_symbol_name(order['instrument'])
                self.open_orders[symbol] = order
                self.logger.info(
                    'Order: [%s] %s %s shares @ %s' % (symbol, order['side'], order['quantity'], order['price']))

    def _is_order_open(self, order):
        return order['state'] == 'queued' or order['state'] == 'unconfirmed' or order['state'] == 'confirmed'

    def _get_symbol_name(self, instrument_url: str):
        return self.robinhood.get_url(instrument_url)['symbol']

    def update_sell_order(self, symbol: str):
        position = self.positions[symbol]
        if position is not None:
            history, errors, errors = self.market.refresh_stock(exchange='', symbol=symbol,
                                                                start_date=datetime.datetime(1990, 1, 1))
            if history is None:
                return
            new_sell_price = round(self.sell_strategy.get_sell_price(history), 2)
            cost_basis = float(position['average_buy_price'])
            # new sell price must larger than cost_basis
            if new_sell_price < cost_basis:
                return
            # new sell price must larger than previous orders
            order = self.open_orders.get(symbol)
            current_sell_price = 0 if order is None else float(order['price'])
            if order is not None and current_sell_price < new_sell_price:
                # cancel current sell order
                res = self.robinhood.session.post('https://api.robinhood.com/orders/%s/cancel/' % order['id'])
                res.raise_for_status()
            if current_sell_price < new_sell_price:
                # place new order with new price
                self._place_stop_limit_order(position['instrument'], int(float(position['quantity'])),
                                             new_sell_price, new_sell_price)
                report = '[{0}] ${1:.2f} ({2:+.2%}) to ${3:.2f} ({4:+.2%})'.format(
                    symbol, current_sell_price, current_sell_price / cost_basis - 1,
                    new_sell_price, new_sell_price / cost_basis - 1
                )
                self.reports.append(report)
                self.logger.info(report)

    def _place_stop_limit_order(self, instrument: str, shares: int, stop_price: float, limit_price: float):
        payload = {
            'account': self.robinhood.get_account()['url'],
            'instrument': instrument,
            'symbol': self._get_symbol_name(instrument),
            'type': 'limit',
            'time_in_force': 'gtc',
            'trigger': 'stop',
            'price': round(limit_price, 2),
            'stop_price': round(stop_price, 2),
            'quantity': shares,
            'side': 'sell'
        }
        res = self.robinhood.session.post(self.robinhood.endpoints['orders'], data=payload)
        res.raise_for_status()


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    logging.config.dictConfig(Utility.get_logging_config())
    seller = ProfitLockSeller()
    if seller.login(username="xinwucheng@gmail.com", password="CHeeSE1982"):
        seller.refresh_account()
        for symbol, position in seller.positions.items():
            try:
                seller.update_sell_order(symbol)
            except Exception as e:
                print("Unexpected error:", e)
