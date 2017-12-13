import pytz
import zipline
from zipline.api import *
from zipline.finance.execution import LimitOrder

from backtest.backtest_utility import BackTestUtility
from strategy.sell.sell_strategy_lock_profit import SimpleProfitLockSellStrategy
from utility.utility import *


def initialize(context):
    BackTestUtility.initialize(context)
    context.sell_strategy_lock_profit = SimpleProfitLockSellStrategy(mini_profit=0)


def handle_data(context, data):
    # analysis based today's market and place orders to execute tomorrow
    stock_list = list(context.screen_assets.keys())
    # place or adjust sell orders for current position
    for position in context.portfolio.positions.values():
        place_sell_orders(context, data, position)
        stock_list.remove(position.asset.symbol)

    # check if it is in the ramp down stage
    if len(stock_list) > 0 and not BackTestUtility.is_ramp_down(context) and \
            context.portfolio.cash > context.fixed_buying_amount:
        available_cash = context.portfolio.cash
        # new buyings
        buyings = context.market.run_strategies(stock_list=stock_list,
                                                target_date=context.datetime.replace(tzinfo=None).date())
        if 'OverReactStrategy' in buyings.keys():
            for stock in buyings['OverReactStrategy'].itertuples():
                asset = context.screen_assets[stock.symbol]
                if data.can_trade(asset):
                    BackTestUtility.cleanup_open_orders(asset)
                    order_target_value(asset, context.fixed_buying_amount,
                                       style=LimitOrder(data.current(asset, 'close')))
                    available_cash -= context.fixed_buying_amount
                    if available_cash < context.fixed_buying_amount:
                        break

    # print today's summary with orders placed before
    BackTestUtility.print_daily_summary(context)


def place_sell_orders(context, data, position):
    price_history = data.history(position.asset, ['high', 'low', 'close'], 30, '1d')
    price_history.index.name = 'date'
    new_sell_price = context.sell_strategy_lock_profit.get_sell_price(price_history, context.datetime.date())
    open_orders = get_open_orders(position.asset)
    current_sell_price = 0 if len(open_orders) == 0 else open_orders[0].limit or open_orders[0].stop

    if new_sell_price > current_sell_price:
        BackTestUtility.cleanup_open_orders(position.asset)
        order(position.asset, -position.amount, stop_price=new_sell_price, limit_price=new_sell_price)


if __name__ == '__main__':
    perf = zipline.run_algorithm(start=datetime.datetime(2017, 1, 10).replace(tzinfo=pytz.UTC),
                                 end=datetime.datetime(2017, 11, 1).replace(tzinfo=pytz.UTC),
                                 initialize=initialize,
                                 handle_data=handle_data,
                                 analyze=BackTestUtility.print_final_summary,
                                 capital_base=100000,
                                 data_frequency='daily',
                                 bundle='quantopian-quandl')
    perf.to_csv('simulation.csv')
