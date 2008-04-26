class Money:
    '''
    I represent a monetary value in a certain currency.
    The value is *always* stored as in integer
    '''
    def __init__(self, currency, value):
        self.currency = currency
        self.value = value
    def to_float(self):
        return self.currency.money_to_float(self)
    def to_str(self):
        return str(self)
    def __str__(self):
        return self.currency.money_to_str(self)
        
class Currency:
    '''I am a currency. It is my job to format Money values'''
    def __init__(self, format, precision):
        self.format = format
        self.precision = precision
    def money_to_float(self, money):
        return float(money.value)/pow(10,self.precision)
    def money_to_str(self, money):
        return self.format%self.money_to_float(money)
    def parse_value(self, value):
        return Money(self, int(round(float(value)*pow(10,self.precision))))
        
class Mint:
    '''I make money'''
    def __init__(self):
        self.currencies = {}
        self.default_currency = None
    def register_currency(self, name, currency):
        self.currencies[name.lower()] = currency
    def get_currency(self, name=None):
        if name is None:
            name = self.default_currency
        return self.currencies[name.lower()]
    def make_money(self, value, currency=None):
        if currency is None:
            currency = self.default_currency
        return Money(self.currencies[currency.lower()], value)

mint = Mint()
