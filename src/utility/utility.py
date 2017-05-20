import datetime
import glob
import json
import os
from collections import namedtuple
from enum import Enum


# public enums
class Market(Enum):
    US = 'us'
    China = 'china'


class DataFolder(Enum):
    Stock = 'stocks'
    Stock_History = os.path.join(Stock, 'history')
    Stock_Listing = os.path.join(Stock, 'listing')
    Output = 'output'


class ListingField(Enum):
    Symbol = 'Symbol'
    Name = 'Name'
    Sector = 'Sector'
    Industry = 'Industry'
    IPO = 'IPO'


class StockPriceField(Enum):
    Date = 'date'
    Open = 'open'
    Close = 'close'
    High = 'high'
    Low = 'low'
    Volume = 'volume'
    AdjustPrice = 'adjust_price'


class Utility:
    # private static objects
    __logging_config = None
    __program_config = None

    @staticmethod
    def get_logging_config(filename='configs/logging_config.json'):
        if Utility.__logging_config is None:
            with open(filename) as config:
                Utility.__logging_config = json.load(config)
        return Utility.__logging_config

    @staticmethod
    def get_config(market: Market = None, filename='configs/program_config.json'):
        if Utility.__program_config is None:
            with open(filename) as config:
                Utility.__program_config = json.load(config,
                                                     object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        if Market.US == market:
            return Utility.__program_config.us
        elif Market.China == market:
            return Utility.__program_config.china
        else:
            return Utility.__program_config

    @staticmethod
    def get_data_folder(market: Market, folder: DataFolder) -> str:
        folder_path = os.path.join(Utility.get_config().data_path, market.value, folder.value)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    @staticmethod
    def get_stock_listing_xlsx(market: Market, latest: bool = False, day: datetime = datetime.date.today()) -> str:
        listing_folder = Utility.get_data_folder(market, DataFolder.Stock_Listing)
        if latest:
            # return latest listing file from the listing folder
            files = glob.glob(os.path.join(listing_folder, 'listing_*.xlsx'))
            if not files:
                raise FileExistsError('Cannot find latest stock listing file in %s' % listing_folder)
            return files[-1]
        else:
            # return file with date stamp as $day
            return os.path.join(listing_folder, 'listing_%s.xlsx' % day.isoformat())

    @staticmethod
    def get_stock_price_history_file(market: Market, symbol: str, ipo_year: str, exchange: str = None):
        history_folder = Utility.get_data_folder(market, DataFolder.Stock_History)
        file_name = '%s-%s-%s.csv' % (exchange, ipo_year, symbol)
        return os.path.join(history_folder, file_name)
