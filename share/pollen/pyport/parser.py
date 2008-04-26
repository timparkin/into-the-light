import re

REGEX = 'from\s+([a-zA-Z\.]+)(\s+as\s+([a-zA-Z_]+))?(\s+(where|order\s+by)\s+(.*))?'

class Parser:
    '''Query parser'''
    
    pattern = None
        
    def parse(self, query):
        
        # Compile the regex if not already done
        if Parser.pattern is None:
            Parser.pattern = re.compile(REGEX, re.I)
        
        # Use regex to pull most of the query apart
        match = Parser.pattern.match(query)
        
        # Retrieve the easy bits
        _table = match.groups()[0]
        _as = match.groups()[2]
        _ending_prefix = match.groups()[4]
        _ending = match.groups()[5]
        
        # If _ending_prefix is not None then it will be 'where' or 'order by'.
        # If it's 'where' then there may be an order by clause in there too.
        if _ending_prefix is None:
            _where = None
            _order_by = None
        else:
            _ending_prefix = ' '.join(_ending_prefix.lower().split())
            if _ending_prefix == 'where':
                if _ending.find('order by') == -1:
                    _where = _ending
                    _order_by = None
                else:
                    _where, _order_by = [s.strip() for s in _ending.split('order by')]
            if _ending_prefix == 'order by':
                _where = None
                _order_by = _ending
        return _table, _as, _where, _order_by

