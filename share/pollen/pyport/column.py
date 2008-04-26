class Column(object):
    '''Base column type to support the concrete column types'''
    def __init__(self, name=None):
        self.name = name
    def __repr__(self):
        return "%s(name='%s')" % (self.__class__.__name__, self.name)

class Integer(Column):
    '''Used for all SQL data types that store whole numbers'''
    pass

class Real(Column):
    '''Used for all SQL data types that store real numbers'''
    pass

class String(Column):
    '''Used for all SQL data types that store character strings'''
    pass

class Date(Column):
    '''Used for the SQL DATE data type'''
    pass

class Time(Column):
    '''Used for the SQL TIME data type'''
    pass

class DateTime(Column):
    '''Used for the SQL TIMESTAMP data type'''
    pass

