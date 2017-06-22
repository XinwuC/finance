import re

import pandas
import pytz
import zipline
from zipline.api import *
from zipline.finance.execution import LimitOrder

from stock.us.us_market import UsaMarket
from utility.utility import *


def initialize(context):
    # init params
    Utility.reset_config(filename='src/backtest/overreact_config.json')

    context.indicator = pandas.read_csv('src/backtest/^GSPC.csv', index_col=0, parse_dates=True, na_values='null')
    context.indicator.Close = context.indicator['Adj Close']
    del context.indicator['Adj Close']
    context.indicator = context.indicator[
                        context.sim_params.start_session - datetime.timedelta(days=30):
                        context.sim_params.end_session]
    context.indicator['sma5'] = context.indicator.Close.rolling(window=5).mean()
    context.indicator['sma10'] = context.indicator.Close.rolling(window=10).mean()
    set_commission(zipline.finance.commission.PerTrade(cost=0))
    context.market = UsaMarket()
    context.long_position = False
    context.buying_power = context.portfolio.cash / 10
    context.screen_assets = {}
    context.orders = {}
    # check valid symbols
    with os.scandir(Utility.get_data_folder(market=Market.US, folder=DataFolder.Stock_History)) as it:
        name_pattern = re.compile(r'\w+-\w+-\w+.csv')
        name_extractor = re.compile(r'\w+')
        for entry in it:
            if entry.is_file() and name_pattern.match(entry.name):
                (exchange, ipo, symbolName, dummy) = name_extractor.findall(entry.name)
                try:
                    asset = symbol(symbolName)
                    context.screen_assets[symbolName] = asset
                except:
                    pass


def before_trading_start(context, data):
    sma5_yesterday = context.indicator.sma5.shift(1)[context.datetime.date()]
    sma5_today = context.indicator.sma5[context.datetime.date()]
    sma10_today = context.indicator.sma10[context.datetime.date()]
    context.long_position = True  # sma5_today > sma5_yesterday and sma5_today > sma10_today
    print('Backtesting for date %s: Portfolio: $%.2f, Cash: $%.2f' % (
        context.datetime.date(), context.portfolio.portfolio_value, context.portfolio.cash))
    print('\tLong Position: {0} (SMA5 Slop: {1:.2%}, SMA5/SMA10: {2:.2%})'.format(context.long_position,
                                                                                  sma5_today / sma5_yesterday - 1,
                                                                                  sma5_today / sma10_today - 1))


def handle_data(context, data):
    stock_list = list(context.screen_assets.keys())
    # print order status
    for transaction_list in context.perf_tracker.todays_performance.processed_transactions.values():
        for transaction in transaction_list:
            if transaction.asset not in context.orders:
                context.orders[transaction.asset] = [transaction]
            else:
                context.orders[transaction.asset].append(transaction)
            if transaction.amount > 0:
                cleanup_orders(transaction.asset)
                order(transaction.asset, -transaction.amount, style=LimitOrder(transaction.price * 1.05))
            print('\t\t\t[%s] Executed %s: \t%s @ $%.2f' % (
                transaction.dt.date(), transaction.asset, transaction.amount, transaction.price,))
    # check and short positions
    for position in context.portfolio.positions.values():
        if context.trading_calendar.session_distance(context.orders[position.asset][-1].dt, context.datetime) > 7:
            cleanup_orders(position.asset)
            order(position.asset, -position.amount, position.cost_basis)
        if context.trading_calendar.session_distance(context.orders[position.asset][-1].dt, context.datetime) > 90:
            cleanup_orders(position.asset)
            order(position.asset, -position.amount, position.cost_basis * 0.95)
        if context.trading_calendar.session_distance(context.orders[position.asset][-1].dt, context.datetime) > 300:
            cleanup_orders(position.asset)
            order(position.asset, -position.amount)
        print('\t\t- %s:\t%s @ $%.2f ($%.2f, $%.2f)' % (
            position.asset, position.amount, position.cost_basis, position.last_sale_price, position.cost_basis * 1.05))
        stock_list.remove(position.asset.symbol)

    # check indicator position
    if not context.long_position:
        return
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
            asset = context.screen_assets[stock.symbol]
            if data.can_trade(asset):
                cleanup_orders(asset)
                order_target_value(asset, context.buying_power, style=LimitOrder(data.current(asset, 'close')))
                cash -= buying_power
                buying_power = min(context.buying_power, cash)
                if buying_power <= 0:
                    break


def analysis(context, perf=None):
    for asset in context.orders.keys():
        print('Asset %s performance: ' % asset)
        for i in range(len(context.orders[asset]) // 2):
            buy = context.orders[asset][i * 2]
            sell = context.orders[asset][i * 2 + 1]
            print('\t- ({2:+.2%}) ${0:+.2f} @ {1} shares for {3} days (${4:.2f}@{5} - ${6:.2f}@{7})'.format(
                buy.amount * (sell.price - buy.price), buy.amount, (sell.price / buy.price - 1),
                (sell.dt - buy.dt).days,
                buy.price, buy.dt.date(), sell.price, sell.dt.date()))
    print('Total return: {0:+.2%} {1:+.2f}'.format(
        context.portfolio.portfolio_value / context.portfolio.starting_cash - 1,
        context.portfolio.portfolio_value - context.portfolio.starting_cash))


def cleanup_orders(asset):
    # cancel all open orders first
    for open_orders in get_open_orders().values():
        for open_order in open_orders:
            if open_order.sid == asset:
                cancel_order(open_order)


if __name__ == '__main__':
    perf = zipline.run_algorithm(start=datetime.datetime(2015, 7, 1).replace(tzinfo=pytz.UTC),
                                 end=datetime.datetime(2016, 7, 1).replace(tzinfo=pytz.UTC),
                                 initialize=initialize,
                                 handle_data=handle_data,
                                 before_trading_start=before_trading_start,
                                 analyze=analysis,
                                 capital_base=10000,
                                 data_frequency='daily',
                                 bundle='quantopian-quandl')
    perf.to_csv('simulation.csv')
