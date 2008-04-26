from cStringIO import StringIO
from twisted.internet import defer
from twisted.internet.interfaces import IFinishableConsumer, IPullProducer
from twisted.python import log


class File(object):
    __implements__ = IPullProducer,
    
    consumer = None
    deferred = None
    
    def __init__(self, filelikeOrPath):
        if hasattr(filelikeOrPath, 'read'):
            self.file = filelikeOrPath
        else:
            self.file = open(filelikeOrPath, 'rb')
        self.consumer = None
        self.deferred = defer.Deferred()
        
    def resumeProducing(self):
        data = self.file.read(1024*32)
        if data:
            self.consumer.write(data)
        else:
            self.consumer.unregisterProducer()
            self.consumer.finish()
            self.deferred.callback(None)
            
    def pauseProducing(self):
        pass
    
    def stopProducing(self):
        log.debug('File.stopProducing')
        self.file.close()
        self.consumer.unregisterProducer()
        self.deferred.errback(None)

        
class PutFileConsumer(object):
    __implements__ = IFinishableConsumer,
    
    def __init__(self):
        self.io = StringIO()
        self.deferred = defer.Deferred()
    
    def registerProducer(self, producer, streaming):
        self.producer = producer
        
    def unregisterProducer(self):
        self.producer = None
        
    def write(self, data):
        self.io.write(data)
        
    def finish(self):
        log.debug('StorConsumer: upload complete, firing deferred')
        self.io.seek(0)
        self.deferred.callback(self.io)
        
