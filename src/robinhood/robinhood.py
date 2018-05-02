from Robinhood import Robinhood

from robinhood.robinhood_utility import RobinhoodUtility


class RobinhoodAccount:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.robinhood = Robinhood()
        self.loggedin = False

    def __enter__(self):
        if self.loggedin:
            self.logout()
        self.login()

    def __exit__(self, *args):
        self.logout()

    def login(self):
        self.loggedin = self.robinhood.login(self.username, self.password)
        return self.loggedin

    def logout(self):
        self.robinhood.logout()

    def get_positions(self):
        positions = {}
        for pos in self.robinhood.securities_owned()['results']:
            symbol = RobinhoodUtility.instrument_2_symbol(pos['instrument'])
            pos['symbol'] = symbol
            positions[symbol] = pos
        return positions

    def cancel_all_orders(self, symbol: str):
        for order in self.robinhood.order_history()['results']:
            if RobinhoodUtility.is_order_open(order):
                if symbol == RobinhoodUtility.instrument_2_symbol(order['instrument']):
                    self.cancel_order(order)

    def cancel_order(self, order):
        res = self.robinhood.session.post('https://api.robinhood.com/orders/%s/cancel/' % order['id'])
        res.raise_for_status()

    def place_stop_limit_sell_order(self, position, limit_price: float, stop_price: float = None,
                                    time_in_force: str = 'GFD',
                                    shares: int = None):
        self.robinhood.place_stop_limit_sell_order(instrument_URL=position['instrument'],
                                                   symbol=position['symbol'],
                                                   time_in_force=time_in_force,
                                                   price=limit_price,
                                                   stop_price=stop_price or limit_price,
                                                   quantity=shares or int(float(position['quantity'])))
