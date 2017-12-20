import six

if six.PY3:
    from robinhood.Robinhood import Robinhood
else:
    from robinhood import Robinhood
