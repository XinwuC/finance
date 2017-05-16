"""
Strategy: capture over-react price drop for sudden events
"""

import datetime
import logging
import numpy
import dateutil
import pandas

from strategy.strategy import Strategy


class OverReactStrategy(Strategy):
    def __init__(self, top_drop_pct=0.05, target_recover_rate=0.05, recover_days=5, recover_success_rate=0.9,
                 max_allowed_fallback=None, allowed_max_fallback_rate=None):
        """
        
        :param top_drop_pct: 
        :param target_recover_rate: 
        :param recover_success_rate: 
        :param max_allowed_fallback: 
        """
        self.top_drop_pct = top_drop_pct
        self.recover_days = recover_days
        self.target_recover_rate = target_recover_rate
        self.recover_success_rate = recover_success_rate
        self.max_allowed_fallback = -target_recover_rate if max_allowed_fallback is None else max_allowed_fallback
        self.allowed_max_fallback_rate = 1 - recover_success_rate if allowed_max_fallback_rate is None \
            else allowed_max_fallback_rate
        self.logger = logging.getLogger(__name__)

    def analysis(self, market: str, symbol: str, price_history: pandas.DataFrame,
                 target_date: datetime.date = None) -> dict:
        """
        Analysis and trigger if the symbol price has seen over reaction drops for the latest day.
    
        Triggering Criteria:
        - price drop today is more than 95% of history
        - 90% chances the price recovered by 5% within 5 days
    
        :param price_history: a 2-D data frame that has price history  
        :return: True: buying candidate; False: Not buying candidate
        """
        if market is None or symbol is None:
            raise Exception('Invalid Argument: market %s, symbol %s' % (market, symbol))
        if price_history is None:
            raise Exception('None object: price_history')
        if target_date is None or price_history.iloc[dateutil.parser.parse(target_date)] is None:
            target_date = price_history.first_valid_index()
        # condition 0: price dropped on target day
        current_drop_pct = price_history['adjusted_change_percentage'][target_date]
        if numpy.isnan(current_drop_pct) or current_drop_pct >= 0:
            return None
        # condition 1: price drops is bigger than 95% of history drops
        drop_history = price_history[price_history.adjusted_change_percentage < 0]
        top_drops = drop_history[drop_history.adjusted_change_percentage <= current_drop_pct]
        if top_drops.shape[0] / drop_history.shape[0] > self.top_drop_pct:
            return None
        # condition 2: price recovered by 5% more within 5 days
        hit_target_price_count = 0
        hit_max_fallback_count = 0
        for date in top_drops.index.tolist():
            buy_price = price_history["Adj Close"].shift(1)[date]
            target_price = buy_price * (1 + self.target_recover_rate)
            fallback_price = buy_price * (1 + self.max_allowed_fallback)
            hit_target_price = False
            last_price = buy_price
            index = price_history.index.get_loc(date) - 1
            for day in range(1, self.recover_days + 1):
                if index - day >= 0:
                    if price_history["Adj Close"].iloc[index - day] > target_price:
                        hit_target_price = True
                        break
                    else:
                        last_price = price_history["Adj Close"].iloc[index - day]
            if hit_target_price:
                hit_target_price_count += 1
            elif last_price < fallback_price:
                hit_max_fallback_count += 1
        if hit_target_price_count / top_drops.shape[0] > self.recover_success_rate \
                and hit_max_fallback_count / top_drops.shape[0] < self.allowed_max_fallback_rate:
            self.logger.info('Overreact Strategy: %s [%s] %s buying %s -> selling %s' % (
                target_date, market, symbol, buy_price, target_price))
            return pandas.Series({'date': target_date, 'market': market, 'symbol': symbol,
                                  'buying_price': buy_price,
                                  'target_price': target_price,
                                  'drop_pct': current_drop_pct,
                                  'top_drop_count': top_drops.shape[0],
                                  'drop_count': drop_history.shape[0],
                                  'top_drop_ratio': top_drops.shape[0] / drop_history.shape[0],
                                  'hit_targets': hit_target_price_count,
                                  'hit_target_ratio': hit_target_price_count / top_drops.shape[0],
                                  'hit_max_fallback': hit_max_fallback_count,
                                  'max_fallback_ratio': hit_max_fallback_count / top_drops.shape[0]
                                  }, index=['date', 'market', 'symbol', 'buying_price', 'target_price', 'drop_pct',
                                            'top_drop_count', 'drop_count', 'top_drop_ratio', 'hit_targets',
                                            'hit_target_ratio', 'hit_max_fallback', 'max_fallback_ratio'])
        else:
            return None
