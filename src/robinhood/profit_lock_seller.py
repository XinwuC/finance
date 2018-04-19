import datetime
import logging

from Robinhood import Robinhood
from stock.us_market import UsaMarket
from strategy.sell.sell_strategy_lock_profit import SimpleProfitLockSellStrategy


class ProfitLockSeller:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.market = UsaMarket()
        self.sell_strategy = SimpleProfitLockSellStrategy()
        self.robinhood = Robinhood()
        self.positions = {}
        self.open_orders = {}
        self.reports = []

    def login(self, username, password):
        return self.robinhood.login(username, password)

    def refresh_account(self):
        # get positions
        self.positions.clear()
        for pos in self.robinhood.securities_owned()['results']:
            symbol = self._get_symbol_name(pos['instrument'])
            self.positions[symbol] = pos
        # get open orders first
        self.open_orders.clear()
        for order in self.robinhood.order_history()['results']:
            if self._is_order_open(order):
                symbol = self._get_symbol_name(order['instrument'])
                self.open_orders[symbol] = order

    def _is_order_open(self, order):
        return order['state'] == 'queued' or order['state'] == 'unconfirmed' or order['state'] == 'confirmed'

    def _get_symbol_name(self, instrument_url: str):
        return self.robinhood.get_url(instrument_url)['symbol']

    def update_sell_order(self, symbol: str):
        position = self.positions[symbol]
        if position is not None:
            # get position data
            shares = int(float(position['quantity']))
            cost_basis = float(position['average_buy_price'])
            report = '[%s] %d shares @ $%.2f' % (symbol, shares, cost_basis)
            # get current sell order data
            order = self.open_orders.get(symbol)
            current_sell_price = 0.00 if order is None else float(order['price'])
            report += ', current sell order: $%.2f' % current_sell_price
            # calculate new sell price
            history = self.market.refresh_stock(symbol=symbol, start=datetime.datetime(1990, 1, 1))
            new_sell_price = round(self.sell_strategy.get_sell_price(cost_basis, history), 2)
            report += ', suggest: ${0:.2f} ({1:+.2%}, ${2:+.2f})'.format(new_sell_price,
                                                                         new_sell_price / cost_basis - 1,
                                                                         (new_sell_price - cost_basis) * shares)
            # update sell order if conditions are met
            if new_sell_price > cost_basis and new_sell_price > current_sell_price:
                if order is not None:
                    # cancel current sell order
                    res = self.robinhood.session.post('https://api.robinhood.com/orders/%s/cancel/' % order['id'])
                    res.raise_for_status()
                # place new order with new price
                self._place_stop_limit_order(position['instrument'], shares, new_sell_price, new_sell_price)
                report += ', new order placed'
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
