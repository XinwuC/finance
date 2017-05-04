from setuptools import setup

setup(
    # Application name:
    name="finance",

    # Version number (initial):
    version="0.1.0",

    # Application author details:
    author="Xinwu",

    # Packages
    # packages=["finance"],

    # Include additional files into the package
    # include_package_data=True,

    # Details
    # url="http://pypi.python.org/pypi/MyApplication_v010/",

    #
    # license="LICENSE.txt",
    # description="Useful towel-related stuff.",

    # long_description=open("README.txt").read(),

    # Dependent packages (distributions)
    install_requires=[
        "Bottleneck",
        "matplotlib",
        "numexpr",
        "numpy",
        "dateutil",
        "pandas",
        "pandas-datareader",
        "scipy",
        "xlrd"
    ],
)
