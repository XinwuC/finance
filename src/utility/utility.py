import datetime
import glob
import json
import os
from collections import namedtuple
from enum import Enum

import pandas as pd
from cryptography.fernet import Fernet

from utility.data_utility import DataUtility


# public enums
class Market(Enum):
    US = 'us'
    China = 'china'


class DataFolder(Enum):
    Stock = 'stocks'
    Stock_History = os.path.join(Stock, 'history')
    Stock_Listing = os.path.join(Stock, 'listing')
    Stock_Model = os.path.join(Stock, 'models')
    Stock_Training = os.path.join(Stock, 'training')
    Output = 'output'


class ListingField(Enum):
    Symbol = 'Symbol'
    Name = 'Name'
    Sector = 'Sector'
    Industry = 'Industry'
    IPO = 'IPO'


class StockPriceField(Enum):
    Symbol = 'symbol'
    Date = 'date'
    Open = 'open'
    Close = 'close'
    High = 'high'
    Low = 'low'
    Volume = 'volume'


class Utility:
    # private static objects
    __logging_config = None
    __program_config = None
    __encrypt_key = b'wCh3acjYDuMj66s_ZSCFQYXBQcYpRaa2dt0Dd7L1q1g='
    __cipher_suite = Fernet(__encrypt_key)

    @staticmethod
    def get_logging_config(filename='configs/logging_config.json'):
        if Utility.__logging_config is None:
            with open(filename) as config:
                Utility.__logging_config = json.load(config)
        return Utility.__logging_config

    @staticmethod
    def reset_config(filename='configs/program_config.json'):
        Utility.__program_config = None
        return Utility.get_config(filename=filename)

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
    def get_stock_hyperlink(market: Market, symbol: str) -> str:
        return '<a href="{0}/{1}">{1}</a>'.format(Utility.get_config(Market(market)).symbol_page, symbol)

    @staticmethod
    def get_data_folder(folder: DataFolder, market: Market = None) -> str:
        folder_path = os.path.join(Utility.get_config().data_path, '' if market is None else market.value, folder.value)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    @staticmethod
    def get_stock_listing_xlsx(market: Market, latest: bool = False, day: datetime = datetime.date.today()) -> str:
        listing_folder = Utility.get_data_folder(market=market, folder=DataFolder.Stock_Listing)
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
    def get_stock_price_history_file(market: Market, symbol: str):
        history_folder = Utility.get_data_folder(market=market, folder=DataFolder.Stock_History)
        file_name = '%s.csv' % symbol
        return os.path.join(history_folder, file_name)

    @staticmethod
    def load_stock_price(market: Market, symbol: str) -> pd.DataFrame:
        file = os.path.join(Utility.get_data_folder(market=market, folder=DataFolder.Stock_History), '%s.csv' % symbol)
        files = glob.glob(file)
        if not files:
            raise FileExistsError('Cannot file: %s' % file)
        price = pd.read_csv(files[0], index_col=0, parse_dates=True)
        DataUtility.calibrate_price_history(price)
        return price

    @staticmethod
    def decrypt(cipher_text: str) -> str:
        if isinstance(cipher_text, bytes):
            return Utility.__cipher_suite.decrypt(cipher_text).decode('utf-8')
        elif isinstance(cipher_text, str) and cipher_text.strip():
            return Utility.__cipher_suite.decrypt(cipher_text.strip().encode('utf-8')).decode('utf-8')
        else:
            return ''

    @staticmethod
    def encrypt(text: str) -> str:
        if isinstance(text, bytes):
            return Utility.__cipher_suite.encrypt(text).decode('utf-8')
        elif isinstance(text, str) and text.strip():
            return Utility.__cipher_suite.encrypt(text.strip().encode('utf-8')).decode('utf-8')
        else:
            return ''
