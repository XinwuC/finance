from pyspark import SparkConf, SparkContext, SQLContext
from pyspark.sql import SparkSession


class SparkUtility:
    # spark context
    __spark_conf = None
    __spark_context = None
    __spark_sql_context = None
    __spark_session = None

    @staticmethod
    def get_spark_conf() -> SparkConf:
        if SparkUtility.__spark_conf is None:
            SparkUtility.__spark_conf = SparkConf()
            SparkUtility.__spark_conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        return SparkUtility.__spark_conf

    @staticmethod
    def get_spark_context() -> SparkContext:
        if SparkUtility.__spark_context is None:
            SparkUtility.__spark_context = SparkContext(conf=SparkUtility.get_spark_conf())
        return SparkUtility.__spark_context

    @staticmethod
    def get_spark_sql_context() -> SparkContext:
        if SparkUtility.__spark_sql_context is None:
            SparkUtility.__spark_sql_context = SQLContext(SparkUtility.get_spark_context())
        return SparkUtility.__spark_sql_context

    @staticmethod
    def get_spark_session() -> SparkSession:
        if SparkUtility.__spark_session is None:
            SparkUtility.__spark_session = SparkSession(SparkUtility.get_spark_context())
        return SparkUtility.__spark_session
