class Stock:
    def __init__(self, symbol: str, name: str = None, ipo_year: str = None, sector: str = None, industry: str = None):
        self._symbol = symbol
        self._name = name or ''
        self._ipo_year = ipo_year or ''
        self._sector = sector or ''
        self._industry = industry or ''
        self.price = None

    @property
    def symbol(self):
        return self._symbol

    @property
    def name(self):
        return self._name

    def set_metadata(self, name: str = None, ipo_year: str = None, sector: str = None, industry: str = None):
        self._name = name or self._name
        self._ipo_year = ipo_year or self._ipo_year
        self._sector = sector or self._sector
        self._industry = industry or self._industry


