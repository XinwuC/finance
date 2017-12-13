import re

import pandas
import pytz
import zipline
from zipline.api import *
from zipline.finance.execution import LimitOrder

from stock.us.us_market import UsaMarket
from backtest.backtest_utility import BackTestUtility
from utility.utility import *


def initialize(context):
    BackTestUtility.initialize(context)


def handle_data(context, data):
    # print today's summary with orders placed before
    BackTestUtility.print_daily_summary(context)
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


def place_sell_orders(context, data, position):
    BackTestUtility.cleanup_open_orders(position.asset)

    trading_days_since_bought = context.trading_calendar.session_distance(
        context.transaction_history[position.asset][-1].dt, context.datetime)

    if trading_days_since_bought > 14:
        order(position.asset, -position.amount, limit_price=position.cost_basis)
    elif trading_days_since_bought > 90:
        order(position.asset, -position.amount, limit_price=position.cost_basis * 0.95)
    elif trading_days_since_bought > 300:
        order(position.asset, -position.amount)
    else:
        order(position.asset, -position.amount, limit_price=position.cost_basis * 1.05)


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
