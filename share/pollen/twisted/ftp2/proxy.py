'''
FTP proxy server.
'''

from twisted.internet import protocol
from twisted.python import components
from twisted.protocol import basic


class FTPProxyProtocol(basic.LineReceiver):
    pass


class FTPProxyFactory(protocol.ServerFactory):
    protocol = FTPProxyProtocol
    
    def __init__(self, strategy):
        self.strategy = strategy
    

class IFTPProxyStrategy(components.Interface):
    pass
    

class UsernameStrategy(object):
    __implements__ = IFTPProxyStrategy,
    
    def __init__(self, mapping):
        self.mapping = mapping
