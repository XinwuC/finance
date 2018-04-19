import logging.config
import math
import talib.abstract
import numpy as np
from matplotlib import pyplot

from keras import Sequential
from keras.layers import Dense, Dropout, GRU

from utility.utility import *
from stock.us_market import UsaMarket, UsaIndex


class lstm:
    def __init__(self, market: Market = Market.US):
        self.model = None
        self.market = market
        # load market indicator
        sp500 = self.add_features(self.load_stock_data(UsaIndex.SP500.name))
        vix = self.add_features(self.load_stock_data(UsaIndex.VIX.name))
        self.market_indicator = pd.concat([sp500, vix], axis=1, join='inner').dropna()

    def add_features(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        ohlcv = ohlcv.astype(np.double)
        # add SMA 5, 30, 90, 180
        for feature in set([StockPriceField.Close.value, StockPriceField.Volume.value]).intersection(ohlcv.columns):
            for sma in [5, 30, 90, 180]:
                ohlcv['%s_sma_%s' % (feature, sma)] = talib.abstract.SMA(ohlcv, timeperiod=sma, price=feature)
        # new features
        open_close_ratio = ohlcv[StockPriceField.Open.value] / ohlcv[StockPriceField.Close.value] - 1
        high_close_ratio = ohlcv[StockPriceField.High.value] / ohlcv[StockPriceField.Close.value] - 1
        low_close_ratio = ohlcv[StockPriceField.Low.value] / ohlcv[StockPriceField.Close.value] - 1
        # normalize by pct_change
        ohlcv = ohlcv.pct_change()
        # append new features
        ohlcv['open_close_ratio'] = open_close_ratio
        ohlcv['high_close_ratio'] = high_close_ratio
        ohlcv['low_close_ratio'] = low_close_ratio
        # drop na
        ohlcv.dropna(inplace=True)
        return ohlcv

    def create_labels(self, ohlcv: pd.DataFrame, timesteps: int):
        next_high_pct_change = ohlcv[StockPriceField.High.value].pct_change().shift(-1)
        future_high = ohlcv[StockPriceField.High.value][::-1].rolling(window=timesteps, min_periods=1).max()[::-1]
        return pd.DataFrame({  # 'is_future_higher': future_high / ohlcv[StockPriceField.High.value] - 1 > 0.02,
            'next_high_pct_change': next_high_pct_change}).astype(np.double)

    def load_stock_data(self, symbol: str, drop_columns=[]) -> pd.DataFrame:
        data = Utility.load_stock_price(self.market, symbol)
        del data[StockPriceField.Symbol.value]
        for drop_col in drop_columns:
            del data[drop_col]
        return data

    def prepare_data(self, symbol: str, timesteps, validate_pct: float = 0.2, test_pct: float = 0.2):
        base_data = self.load_stock_data(symbol)
        label = self.create_labels(ohlcv=base_data, timesteps=timesteps)
        base_data = self.add_features(base_data)
        # combine with sp500
        base_data = pd.concat([base_data, self.market_indicator], axis=1, join='inner').dropna()
        training_steps = [base_data]
        for step in range(timesteps, 0, -1):
            one_step = base_data.shift(step)
            one_step.columns = ['%s(-%d)' % (col, step) for col in base_data.columns]
            training_steps.append(one_step)
        featured_data = pd.concat(training_steps, axis=1, join='inner').dropna()

        input = featured_data.iloc[:, base_data.shape[1]:].values
        output = label.ix[featured_data.index]
        scaled_input = input.reshape(-1, timesteps, base_data.shape[1])
        scaled_output = output.values

        training_ends = math.floor(scaled_input.shape[0] * (1 - validate_pct - test_pct))
        validate_ends = math.floor(scaled_input.shape[0] * (1 - test_pct))

        training_data = scaled_input[:training_ends]
        training_label = scaled_output[:training_ends]
        validate_data = scaled_input[training_ends:validate_ends]
        validate_label = scaled_output[training_ends:validate_ends]
        test_data = scaled_input[validate_ends:]
        test_label = scaled_output[validate_ends:]
        return training_data, training_label, validate_data, validate_label, test_data, test_label

    def create_model(self, timesteps, feature_size, outputs=1):
        self.model = Sequential()
        self.model.add(GRU(2048, input_shape=(timesteps, feature_size), dropout=0.5))
        self.model.add(Dropout(0.5))
        self.model.add(Dense(outputs))
        self.model.compile(loss='mae', optimizer='adam')

    def train_model(self, train_data, train_label, validation_data, validation_label, epochs, batch_size):
        return self.model.fit(train_data, train_label, validation_data=(validation_data, validation_label),
                              epochs=epochs, batch_size=batch_size, shuffle=False, verbose=2)


if __name__ == '__main__':
    logging.config.dictConfig(Utility.get_logging_config())

    # load market indicators
    refresh_prices = False
    if refresh_prices:
        us = UsaMarket(avkey='M5351LT3XK977PEQ')
        us.refresh_index(UsaIndex.SP500)
        us.refresh_index(UsaIndex.VIX)
        us.refresh_stock('IRBT', datetime.datetime(1982, 1, 1))

    # train models
    timesteps = 10
    lstm = lstm()
    training_data, training_label, vd, vl, td, tl = lstm.prepare_data('IRBT', timesteps)
    lstm.create_model(timesteps=training_data.shape[1],
                      feature_size=training_data.shape[2],
                      outputs=training_label.shape[1])
    train_perf = lstm.train_model(training_data, training_label, vd, vl, epochs=8, batch_size=timesteps * 10)
    # plot history¬
    pyplot.plot(train_perf.history['loss'], label='train')
    pyplot.plot(train_perf.history['val_loss'], label='test')
    pyplot.legend()
    pyplot.show()
    # lstm.train_model()
    that = lstm.model.predict(td)
    for i in range(tl.shape[1]+1):
        pyplot.plot(tl[:, i], label='actual_%s' % i)
        pyplot.plot(that[:, i], label='predict_%s' % i)
    pyplot.legend()
    pyplot.show()
