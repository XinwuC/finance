import re

import numpy as np
import zipline
from zipline.api import *

from stock.us.us_market import UsaMarket
from utility.utility import *


class BackTestUtility:
    @staticmethod
    def initialize(context):
        set_commission(zipline.finance.commission.PerTrade(cost=0))

        context.screen_assets = BackTestUtility.match_screen_assets(context)
        context.transaction_history = {}
        context.market = UsaMarket()
        context.fixed_buying_amount = context.portfolio.cash / 100

    @staticmethod
    def match_screen_assets(context):
        screen_assets = {}
        # check valid symbols
        with os.scandir(Utility.get_data_folder(market=Market.US, folder=DataFolder.Stock_History)) as it:
            name_pattern = re.compile(r'\w+-\w+-\w+.csv')
            name_extractor = re.compile(r'\w+')
            for entry in it:
                if entry.is_file() and name_pattern.match(entry.name):
                    (exchange, ipo, symbolName, dummy) = name_extractor.findall(entry.name)
                    try:
                        asset = symbol(symbolName)
                        screen_assets[symbolName] = asset
                    except:
                        pass
        return screen_assets

    @staticmethod
    def is_ramp_down(context) -> bool:
        trading_days_left = context.trading_calendar.session_distance(context.datetime,
                                                                      context.trading_client.sim_params.end_session)
        return trading_days_left < 7

    @staticmethod
    def cleanup_open_orders(asset):
        for open_order in get_open_orders(asset):
            cancel_order(open_order)

    @staticmethod
    def print_daily_summary(context):
        print('[%s] Cash: $%.2f, Portfolio: $%.2f' % (
            context.datetime.date(), context.portfolio.cash, context.portfolio.portfolio_value))
        # if asset is sold today, print profit summary in the last
        sold_assets = []
        # print today's transactions
        if len(context.perf_tracker.todays_performance.processed_transactions.values()) > 0:
            print('\ttransactions:')
            for transaction_list in context.perf_tracker.todays_performance.processed_transactions.values():
                for transaction in transaction_list:
                    if transaction.asset not in context.transaction_history:
                        context.transaction_history[transaction.asset] = [transaction]
                    else:
                        context.transaction_history[transaction.asset].append(transaction)
                    if transaction.amount > 0:
                        print('\t\t- Buy %s %d @ $%.2f' % (transaction.asset, transaction.amount, transaction.price))
                    else:
                        print('\t\t- Sell %s %d @ $%.2f' % (transaction.asset, transaction.amount, transaction.price))
                        sold_assets.append(transaction.asset)
        # print positions
        if len(context.portfolio.positions.values()) > 0:
            print('\tpositions:')
            for position in context.portfolio.positions.values():
                current_order = get_open_orders(position.asset)
                assert (len(current_order) <= 1)
                current_sell_price = np.nan if len(current_order) == 0 else \
                    current_order[0].limit or current_order[0].stop
                print('\t\t- {0}: {1} @ ${2:.2f} => ${3:.2f} ({4:.2%}), Now ${5:.2f} (${6:+.2f}, {7:+.2%})'.format(
                    position.asset, position.amount, position.cost_basis, current_sell_price,
                    current_sell_price / position.cost_basis - 1, position.last_sale_price,
                    position.amount * (position.last_sale_price - position.cost_basis),
                    position.last_sale_price / position.cost_basis - 1))
        # print today profit summary
        if len(sold_assets) > 0:
            print('\tprofit:')
            for asset in sold_assets:
                buy_transaction = context.transaction_history[asset][-2]
                sell_transaction = context.transaction_history[asset][-1]
                buy_money = buy_transaction.amount * buy_transaction.price
                sell_money = -sell_transaction.amount * sell_transaction.price
                days = (sell_transaction.dt - buy_transaction.dt).days
                print('\t\t- {0}: ${1:+.2f} ({2:+.2%}), {3} @ ${4:.2f} - ${5:.2f} with {6} days'.format(
                    asset, sell_money - buy_money, sell_money / buy_money - 1, buy_transaction.amount,
                    sell_transaction.price, buy_transaction.price, days))

    @staticmethod
    def print_final_summary(context, perf=None):
        for asset in context.transaction_history.keys():
            print('Asset %s performance: ' % asset)
            for i in range(len(context.transaction_history[asset]) // 2):
                buy = context.transaction_history[asset][i * 2]
                sell = context.transaction_history[asset][i * 2 + 1]
                print('\t- ({2:+.2%}) ${0:+.2f} @ {1} shares for {3} days (${4:.2f}@{5} - ${6:.2f}@{7})'.format(
                    buy.amount * (sell.price - buy.price), buy.amount, (sell.price / buy.price - 1),
                    (sell.dt - buy.dt).days,
                    buy.price, buy.dt.date(), sell.price, sell.dt.date()))
        print('Total return: {0:+.2%} {1:+.2f}'.format(
            context.portfolio.portfolio_value / context.portfolio.starting_cash - 1,
            context.portfolio.portfolio_value - context.portfolio.starting_cash))
