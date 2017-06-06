from setuptools import setup

setup(
    # Application name:
    name="stock-bot",

    # Version number (initial):
    version="0.1.0",

    # Application author details:
    author="Xinwu",

    # Packages
    # packages=["finance"],

    # Details
    url="https://github.com/XinwuC/finance",

    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],

    # Dependent packages (distributions)
    install_requires=[
        'tushare>=0.7.7',
        'pandas>=0.18.1',
        'pandas-datareader>=0.4.0',
        'xlrd>=1.0.0',
        'openpyxl>=2.4.7',
        'lxml>=3.7.3',
        'bottleneck>=1.2.1',
        'scipy>=0.19.0',
        'numexpr>=2.6.2',
        'zipline>=1.1.0',
    ],
)
