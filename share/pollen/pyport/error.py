class Error:
    '''Package error class'''
    def __init__(self, message, *args):
        self.message = message
        self.args = args
    def __str__(self):
        return self.message % self.args
        
class ConfigurationError(Error):
    pass

class NoSuchAttributeError(Error):
    pass

class InvalidSyntaxError(Error):
    pass

class SessionExpired(Error):
    '''Needed a session to perform some operation but the session has been
    deleted.'''
