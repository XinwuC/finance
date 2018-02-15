import logging.config
import math
import talib.abstract
from sklearn.preprocessing import MinMaxScaler
from matplotlib import pyplot

from keras import Sequential
from keras.layers import LSTM, Dense, Dropout, GRU

from utility.utility import *


class lstm:
    def __init__(self, market: Market = Market.US):
        self.model = None
        self.market = market
        self.sp500 = self.load_stock_data('^GSPC')

    def add_features(self, ohlcv: pd.DataFrame):
        # add SMA 5, 30, 90, 180
        for feature in [StockPriceField.Close.value]:
            for sma in [5, 30, 90, 180]:
                ohlcv['%s_sma_%s' % (feature, sma)] = talib.abstract.SMA(ohlcv, timeperiod=sma, price=feature)
        # normalize to pct_change
        ohlcv = ohlcv.pct_change()
        # drop na
        ohlcv.dropna(inplace=True)
        return ohlcv

    def load_stock_data(self, symbol: str) -> pd.DataFrame:
        data = Utility.load_stock_price(self.market, symbol)
        del data[StockPriceField.Symbol.value]
        return self.add_features(data)

    def prepare_data(self, symbol: str, timesteps, validate_pct: float = 0.2, test_pct: float = 0.2):
        base_data = self.load_stock_data(symbol)
        # combine with sp500
        base_data = pd.concat([base_data, self.sp500], axis=1, join='inner').dropna()
        training_steps = [base_data]
        for step in range(timesteps, 0, -1):
            one_step = base_data.shift(step)
            one_step.columns = ['%s(-%d)' % (col, step) for col in base_data.columns]
            training_steps.append(one_step)
        featured_data = pd.concat(training_steps, axis=1, join='inner').dropna()
        input = featured_data.iloc[:, base_data.shape[1]:].values
        output = featured_data.iloc[:, 3].values  # close price

        # scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_input = input.reshape(-1, timesteps, base_data.shape[1])
        scaled_output = output

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
    timesteps = 10
    lstm = lstm()
    training_data, training_label, vd, vl, td, tl = lstm.prepare_data('IBM', timesteps)
    lstm.create_model(timesteps=timesteps, feature_size=training_data.shape[2], outputs=1)
    train_perf = lstm.train_model(training_data, training_label, vd, vl, epochs=9, batch_size=timesteps * 10)
    # plot history
    pyplot.plot(train_perf.history['loss'], label='train')
    pyplot.plot(train_perf.history['val_loss'], label='test')
    pyplot.legend()
    pyplot.show()
    # lstm.train_model()
    that = lstm.model.predict(td)
    pyplot.plot(tl, label='actual')
    pyplot.plot(that, label='predict')
    pyplot.legend()
    pyplot.show()

    table = pd.DataFrame({'actual': td, 'predict': that})
    table.to_csv('rnn_predict.csv')
