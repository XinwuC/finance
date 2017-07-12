import logging.config

import pandas
from pyspark.ml.classification import LogisticRegressionModel
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import DataFrame

from utility.spark_utility import SparkUtility
from utility.utility import *


class UpliftPredictionWithLRModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.spark_sql_context = SparkUtility.get_spark_sql_context()
        self.spark_session = SparkUtility.get_spark_session()
        model_path = os.path.join(Utility.get_data_folder(DataFolder.Stock_Model, Market.US), 'lr_model')
        self.model = LogisticRegressionModel.load(model_path)

    @staticmethod
    def label_data(data: pandas.DataFrame) -> pandas.DataFrame:
        data['max'] = data.high.shift(1).rolling(window=5).max()
        data['label'] = data.apply(lambda row: 1 if row.close * 1.05 < row['max'] else 0, axis=1)
        del data['max']
        return data

    @staticmethod
    def generate_features(data: pandas.DataFrame) -> pandas.DataFrame:
        data.loc[:, 'close_pct'] = data.close.pct_change()
        for sma in [5, 30, 90, 180]:
            for feature in ['close', 'volume']:
                col_name = '%s_sma%s' % (feature, sma)
                data.loc[:, col_name] = data[feature].rolling(window=sma).mean()
                data.loc[:, '%s_pct' % col_name] = data[col_name].pct_change()
        return data

    @staticmethod
    def create_spark_data(data: pandas.DataFrame) -> DataFrame:
        spark_data = SparkUtility.get_spark_session().createDataFrame(data)
        spark_data = VectorAssembler(inputCols=[col for col in spark_data.columns if col not in ['label', 'symbol']],
                                     outputCol="features_vector").transform(spark_data)
        return spark_data.na.drop()

    def predict(self, data: DataFrame):
        return self.model.transform(data)
