import logging.config

import pandas

from model.logistic_regression import UpliftPredictionWithLRModel
from strategy.strategy import Strategy
from utility.utility import *


class LogisticRegressionModelStrategy(Strategy):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = UpliftPredictionWithLRModel()

    def analysis(self, price_history: pandas.DataFrame, target_date: datetime.date = None) -> dict:
        # calibrate input
        price_history, target_date = self.calibrate(price_history, target_date)
        if price_history is None or price_history.empty:
            return None
        # prepare data
        price_history = self.model.generate_features(price_history)
        spark_data = self.model.create_spark_data(price_history[target_date:target_date])
        # prediction
        predict = self.model.predict(spark_data).first()
        # post processing
        if predict is not None and predict.probability[1] > 0.5:
            # found buying position
            self.logger.info('LogisticRegressionModel Strategy: %s [%s] buying %s -> selling %s' % (
                target_date, predict.symbol, predict.close, predict.close * 1.05))
            return pandas.Series({'date': target_date,
                                  'symbol': predict.symbol,
                                  'close': predict.close,
                                  'close_pct': predict.close_pct,
                                  'target_price': predict.close * 1.05,
                                  'probability': predict.probability[1]},
                                 index=['date', 'symbol', 'close', 'close_pct', 'target_price', 'probability'])
        else:
            return None
