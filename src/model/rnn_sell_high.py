import logging.config
import math

import numpy as np
import sklearn.metrics as metrics
import talib.abstract
from keras import Sequential
from keras.layers import Dense, Dropout, GRU
from matplotlib import pyplot
from sklearn.preprocessing import MinMaxScaler

from stock.us_market import UsaMarket, UsaIndex
from utility.utility import *


class lstm:
    def __init__(self, market: Market = Market.US):
        self.model = None
        self.market = market
        self.ohlc_columns = [StockPriceField.Open.value,
                             StockPriceField.High.value,
                             StockPriceField.Low.value,
                             StockPriceField.Close.value]
        # load market indicator
        sp500 = self.add_features(self.load_stock_data(UsaIndex.SP500.name))
        vix = self.add_features(self.load_stock_data(UsaIndex.VIX.name))
        sp500.rename(index=str, columns={col: '%s_sp500' % col for col in sp500.columns}, inplace=True)
        vix.rename(index=str, columns={col: '%s_vix' % col for col in vix.columns}, inplace=True)
        self.market_indicator = pd.concat([sp500, vix], axis=1, join='inner').dropna()

    def add_features(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        ohlcv = ohlcv.astype(np.double)
        # add SMA 5, 30, 90, 180
        for feature in set([StockPriceField.Close.value, StockPriceField.Volume.value]).intersection(ohlcv.columns):
            for sma in [5, 30, 90, 180]:
                ohlcv['%s_sma_%s' % (feature, sma)] = talib.abstract.SMA(ohlcv, timeperiod=sma, price=feature)
        # drop na
        ohlcv.dropna(inplace=True)
        return ohlcv

    def normalize_data(self, data: np.ndarray) -> np.ndarray:
        return MinMaxScaler(feature_range=(0, 1)).fit_transform(data)

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

    def drop_correlate_features(self, features: pd.DataFrame, label_col: str):
        del_cols = set()
        corr = features.corr()
        for col_a in features.columns:
            if col_a in del_cols:
                continue
            for col_b in features.columns:
                if col_b == col_a or col_b == label_col:
                    continue
                if corr.loc[col_a, col_b] > 0.9:
                    del_cols.add(col_b)
        for col in del_cols:
            del features[col]

    def prepare_data(self, symbol: str, timesteps: int) -> (np.ndarray, np.ndarray):
        symbol_features = self.add_features(self.load_stock_data(symbol))
        # 1. combine with sp500
        combined_features = pd.concat([symbol_features, self.market_indicator], axis=1, join='inner').dropna()
        self.drop_correlate_features(combined_features, 'high')
        # 2. normalize input data before time steps
        vol_columns = [col for col in combined_features.columns if col.startswith(StockPriceField.Volume.value)]
        price_columns = [col for col in combined_features.columns if col not in vol_columns]
        price_scaler = MinMaxScaler(feature_range=(0, 1)).fit(combined_features[price_columns].values.reshape(-1, 1))
        vol_scaler = MinMaxScaler(feature_range=(0, 1)).fit(combined_features[vol_columns].values.reshape(-1, 1))
        for price_col in price_columns:
            combined_features[price_col] = price_scaler.transform(combined_features[price_col].values.reshape(-1, 1))
        for vol_col in vol_columns:
            combined_features[vol_col] = vol_scaler.transform(combined_features[vol_col].values.reshape(-1, 1))
        assert combined_features.values.min() >= 0 and combined_features.values.max() <= 1.000001
        # 3. add time steps
        training_steps = []
        for step in range(timesteps, 0, -1):
            one_step = combined_features.shift(step)
            one_step.columns = ['%s(-%d)' % (col, step) for col in combined_features.columns]
            training_steps.append(one_step)
        input_timesteps = pd.concat(training_steps, axis=1, join='inner').dropna()
        output_data = combined_features['high'].shift(-1).ix[input_timesteps.index]
        assert input_timesteps.shape[0] == output_data.shape[0]
        # 4. reshape to 3D with timesteps
        input = input_timesteps.values.reshape(-1, timesteps, combined_features.shape[1])
        output = output_data.values.reshape(-1, 1)
        assert input.shape[0] == output.shape[0]
        return input, output

    def split_data(self, input: np.ndarray, output: np.ndarray, validate_pct: float = 0.2, test_pct: float = 0.2):
        assert input.shape[0] == output.shape[0]

        training_ends = math.floor(input.shape[0] * (1 - validate_pct - test_pct))
        validate_ends = math.floor(input.shape[0] * (1 - test_pct))

        training_data = input[:training_ends]
        training_label = output[:training_ends]
        validate_data = input[training_ends:validate_ends]
        validate_label = output[training_ends:validate_ends]
        test_data = input[validate_ends:]
        test_label = output[validate_ends:]
        return training_data, training_label, validate_data, validate_label, test_data, test_label

    def create_model(self, timesteps, feature_size, outputs=1):
        self.model = Sequential()
        self.model.add(GRU(2048, input_shape=(timesteps, feature_size), dropout=0.5))
        self.model.add(Dropout(0.5))
        self.model.add(Dense(outputs))
        self.model.compile(loss='mae', optimizer='adam')

    def train_model(self, train_data, train_label, validation_data, validation_label, epochs, batch_size):
        print('training: %s, label: %s' % (train_data.shape, train_label.shape))
        print('validation: %s, label: %s' % (validation_data.shape, validation_label.shape))
        print('epochs: %s, batch size: %s' % (epochs, batch_size))
        return self.model.fit(train_data, train_label, validation_data=(validation_data, validation_label),
                              epochs=epochs, batch_size=batch_size, shuffle=False, verbose=2)


if __name__ == '__main__':
    logging.config.dictConfig(Utility.get_logging_config())
    symbol = 'IBM'
    # load market indicators
    refresh_prices = False
    if refresh_prices:
        us = UsaMarket(avkey='M5351LT3XK977PEQ')
        us.refresh_index(UsaIndex.SP500)
        us.refresh_index(UsaIndex.VIX)
        us.refresh_stock(symbol, datetime.datetime(1982, 1, 1))

    # train models
    timesteps = 10
    lstm = lstm()
    input, output = lstm.prepare_data(symbol, timesteps)
    training_data, training_label, vd, vl, td, tl = lstm.split_data(input, output)
    lstm.create_model(timesteps=training_data.shape[1],
                      feature_size=training_data.shape[2],
                      outputs=training_label.shape[1])
    train_perf = lstm.train_model(training_data, training_label, vd, vl, epochs=20, batch_size=timesteps * 10)
    # plot history¬
    pyplot.plot(train_perf.history['loss'], label='train')
    pyplot.plot(train_perf.history['val_loss'], label='test')
    pyplot.legend()
    pyplot.show()
    # lstm.train_model()
    that = lstm.model.predict(td)
    for i in range(tl.shape[1]):
        pyplot.plot(tl[:, i], label='actual_%s' % i)
        pyplot.plot(that[:, i], label='predict_%s' % i)
    pyplot.legend()
    pyplot.show()
    print('test loss: ', metrics.mean_absolute_error(tl, that))
