import json
from collections import namedtuple


class Configuration:
    __logging_config = None
    __program_config = None

    @staticmethod
    def get_logging_config(filename='configs/logging_config.json'):
        if Configuration.__logging_config is None:
            with open(filename) as config:
                Configuration.__logging_config = json.load(config)
        return Configuration.__logging_config

    @staticmethod
    def get_us_config(market='us', filename='configs/program_config.json'):
        if Configuration.__program_config is None:
            with open(filename) as config:
                Configuration.__program_config = json.load(config,
                                                           object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        return Configuration.__program_config.us
