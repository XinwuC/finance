import pandas
from utility.utility import *


class DataUtility:
    @staticmethod
    def validate_price_history(price_history: pandas.DataFrame) -> bool:
        '''
        validate price history schema is correct.

        :param price_history: pandas.dataframe to be validated
        :return: true if valid, empty price history is deemed as valid. False if invalid
        '''
        if price_history is None or price_history.empty:
            return True
        elif isinstance(price_history.index[0], datetime.datetime):
            return True
        else:
            return False

    @staticmethod
    def calibrate_price_history(price_history: pandas.DataFrame, target_date: datetime.date = None) \
            -> (pandas.DataFrame, datetime.date):
        '''
        calibrate price history:
        - drop duplicate days in price_history
        - slice price_history from earliest to target_date
        - align target_date to the last day in price_history

        :param price_history:
        :param target_date:
        :return: calibrated price_history and target_date
        '''
        if price_history is None or price_history.empty:
            return None, None
        # remove duplicate index
        price_history = price_history[~price_history.index.duplicated(keep='first')]
        # calibrate target date
        if target_date is None:
            target_date = price_history.index.max().date()
        # condition 0: price dropped on target day
        price_history.sort_index(inplace=True, ascending=True)
        # slicing price_history to keep only up to target_date data
        price_history = price_history[:target_date]
        if price_history.empty:
            return None, None
        if price_history.index[-1].date() != target_date:
            target_date = price_history.index[-1]
        return price_history, target_date
