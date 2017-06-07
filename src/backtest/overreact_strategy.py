import re

import pytz
import zipline
from zipline.api import *
from zipline.finance.execution import LimitOrder

from stock.us.us_market import UsaMarket
from utility.utility import *


def initialize(context):
    # init params
    Utility.reset_config(filename='src/backtest/overreact_config.json')

    set_commission(zipline.finance.commission.PerTrade(cost=0))
    context.market = UsaMarket()
    context.buying_power = context.portfolio.cash / 10
    context.buyings = {}
    context.assets = {}
    # check valid symbols
    with os.scandir(Utility.get_data_folder(market=Market.US, folder=DataFolder.Stock_History)) as it:
        name_pattern = re.compile(r'\w+-\w+-\w+.csv')
        name_extractor = re.compile(r'\w+')
        for entry in it:
            if entry.is_file() and name_pattern.match(entry.name):
                (exchange, ipo, symbolName, dummy) = name_extractor.findall(entry.name)
                try:
                    asset = symbol(symbolName)
                    context.assets[symbolName] = asset
                except:
                    pass
    pass


def handle_data(context, data):
    print('Backtesting for date %s: Portfolio: $%.2f, Cash: $%.2f' % (
        context.datetime.date(), context.portfolio.portfolio_value, context.portfolio.cash))
    stock_list = list(context.assets.keys())
    # cancel all unfilled buy orders
    for open_orders in get_open_orders().values():
        for open_order in open_orders:
            if open_order.amount > 0:
                cancel_order(open_order)
    # check and short positions
    for position in context.portfolio.positions.values():
        if not context.buyings[position.asset][2]:
            # place sell order
            cleanup_orders(position.asset)
            order(position.asset, -position.amount, style=LimitOrder(context.buyings[position.asset][1]))
            context.buyings[position.asset][2] = True
            # print('Sell order %s on %s at %s' % (position.amount, position.asset, context.buyings[position.asset][1]))
        if context.trading_calendar.session_distance(context.buyings[position.asset][0], context.datetime) > 6:
            cleanup_orders(position.asset)
            order(position.asset, -position.amount)
            # print('Sell order %s on %s at market price' % (position.amount, position.asset))
        print('\t- %s:\t%s @ %.2f' % (position.asset, position.amount, position.cost_basis))
        stock_list.remove(position.asset.symbol)
    # print order status
    for transaction_list in context.perf_tracker.todays_performance.processed_transactions.values():
        for transaction in transaction_list:
            print('\t[%s] Executed %s: \t%s @ $%.2f' % (
                transaction.dt.date(), transaction.asset, transaction.amount, transaction.price,))

    # check if it is in the ramp down stage
    if context.trading_calendar.session_distance(context.datetime, context.trading_client.sim_params.end_session) < 7:
        return
    # check if we still have cash to buy
    cash = context.portfolio.cash
    buying_power = min(context.buying_power, cash)
    if buying_power <= 0:
        return
    # new buyings
    buyings = context.market.run_strategies(stock_list=stock_list,
                                            target_date=context.datetime.replace(tzinfo=None).date())
    if 'OverReactStrategy' in buyings.keys():
        for stock in buyings['OverReactStrategy'].itertuples():
            asset = context.assets[stock.symbol]
            if data.can_trade(asset):
                cleanup_orders(asset)
                order_target_value(asset, context.buying_power, style=LimitOrder(stock.buying_price))
                context.buyings[asset] = [context.datetime, stock.sell_price, False]
                cash -= buying_power
                buying_power = min(context.buying_power, cash)
                if buying_power <= 0:
                    break


def cleanup_orders(asset):
    # cancel all open orders first
    for open_orders in get_open_orders().values():
        for open_order in open_orders:
            if open_order.sid == asset:
                cancel_order(open_order)


if __name__ == '__main__':
    perf = zipline.run_algorithm(start=datetime.datetime(2016, 1, 1).replace(tzinfo=pytz.UTC),
                                 end=datetime.datetime(2016, 4, 1).replace(tzinfo=pytz.UTC),
                                 initialize=initialize,
                                 handle_data=handle_data,
                                 capital_base=10000,
                                 data_frequency='daily',
                                 bundle='quantopian-quandl')
    print(perf)
