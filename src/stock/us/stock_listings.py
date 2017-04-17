"""
Get a full listing symbols.

Source provider is http://www.nasdaq.com/screening/company-list.aspx

"""

import datetime
import logging
import os

import pandas
from pandas import ExcelWriter

from configs.configuration import Configuration


class StockListings:
    def __init__(self,
                 provider_url=Configuration.get_us_config().stock_list_provider,
                 markets=Configuration.get_us_config().markets):
        self.logger = logging.getLogger(__name__)
        self.provider_url = provider_url
        self.markets = markets

    def refresh(self,
                location=Configuration.get_us_config().data_path,
                filename=Configuration.get_us_config().symbols_file):
        """
        refresh symbols lists from source provider, and store in sto
        
        :param location: path to the store file
        :param filename: file name to the stored file, actual file name will append _yyyy-mm-dd.xlsx
        :return: void
        """
        os.makedirs(location, exist_ok=True)
        excel_file = os.path.join(location, '%s_%s.xlsx' % (filename, datetime.date.today().isoformat()))
        try:
            with ExcelWriter(excel_file) as writer:
                self.logger.info('Saving stock listings to %s.', excel_file)
                for market in self.markets:
                    try:
                        symbols = pandas.read_csv(self.provider_url % market)
                        symbols.to_excel(writer, market)
                        self.logger.info('Saved stock listings for market %s.', market.upper())
                    except Exception as e:
                        self.logger.error('Fetching stock listings error for market %s: %s', market.upper(), e)
                        self.recover_listings_from_previous_version(market)
        except Exception as e:
            self.logger.error('Saving stock listings failed: %s', e)

    def recover_listings_from_previous_version(self, market):
        pass
