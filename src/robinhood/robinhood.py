from Robinhood import Robinhood


class RobinhoodAccount:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.robinhood = Robinhood()
        self.login()

    def login(self):
        return self.robinhood.login(self.username, self.password)

    def get_positions(self):
        positions = {}
        for pos in self.robinhood.securities_owned()['results']:
            symbol = self._instrument_2_symbol(pos['instrument'])
            pos['symbol'] = symbol
            positions[symbol] = pos
        return positions

    def cancel_all_orders(self, symbol: str):
        for order in self.robinhood.order_history()['results']:
            if self._is_order_open(order):
                if symbol == self._instrument_2_symbol(order['instrument']):
                    self.cancel_order(order)

    def cancel_order(self, order):
        res = self.robinhood.session.post('https://api.robinhood.com/orders/%s/cancel/' % order['id'])
        res.raise_for_status()

    def get_max_trade_price(self, symbol: str, bid_price: bool = True, ask_price: bool = False) -> float:
        trade_prices = self.robinhood.last_trade_price(symbol)
        if bid_price:
            trade_prices += self.robinhood.bid_price(symbol)
        if ask_price:
            trade_prices += self.robinhood.ask_price(symbol)
        return float(max(max(trade_prices)))

    def bid_price(self, symbol: str) -> float:
        return self.robinhood.bid_price(symbol)

    def place_stop_limit_sell_order(self, position, limit_price: float, stop_price: float = None,
                                    time_in_force: str = 'GFD',
                                    shares: int = None):
        self.robinhood.place_stop_limit_sell_order(instrument_URL=position['instrument'],
                                                   symbol=position['symbol'],
                                                   time_in_force=time_in_force,
                                                   price=limit_price,
                                                   stop_price=stop_price or limit_price,
                                                   quantity=shares or int(float(position['quantity'])))

    @staticmethod
    def _is_order_open(order) -> bool:
        return order['state'] == 'queued' or order['state'] == 'unconfirmed' or order['state'] == 'confirmed'

    def _instrument_2_symbol(self, instrument: str) -> str:
        return self.robinhood.get_url(instrument)['symbol']
