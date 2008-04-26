import grp, os, os.path, pwd, shutil, stat
from cStringIO import StringIO
from twisted.application import service
from twisted.cred import credentials, error
from twisted.internet import defer, protocol, reactor
from twisted.internet.interfaces import IFinishableConsumer, IPullProducer
from twisted.protocols import basic
from twisted.python import components, filepath, log

from pollen.twisted.ftp2 import errors, iftp, ftputil
from pollen.twisted.ftp2.ftputil import File, PutFileConsumer


# TYPE Constants
ASCII = 'A'
BINARY = 'I'


PERM_STRINGS = ['---', '--x', '-w-', '-wx', 'r--', 'r-x', 'rw-', 'rwx']
def modeToString(mode):
    perms = mode & 511
    permString = []
    while perms:
        permString.append(PERM_STRINGS[perms&7])
        perms = perms/8
    permString.reverse()
    
    return (stat.S_ISDIR(mode) and 'd' or '-') + ''.join(permString)
       


class FTPServerProtocol(basic.LineReceiver):
    
    USER, PASS, CONNECTED = [object() for i in range(3)]
    
    def connectionMade(self):
        self.sendLine('220 Service ready')
        self.resetState()
        
    def connectionLost(self, reason):
        if self.state is self.CONNECTED and self.logout:
            self.logout()
            
    def resetState(self):
        self.state = self.USER
        self.avatar = None
        self.logout = None
        self.type = ASCII
        
    def lineReceived(self, line):
        log.debug('--> %r'%line)
        unpack = line.split(None, 1)
        command, args = unpack[0], unpack[1:]
        try:
            handler = getattr(self, 'ftp_%s'%command.upper())
        except AttributeError:
            self.sendLine('502 Command not implemented')
            return
        d = defer.maybeDeferred(handler, *args)
        d.addErrback(self._error)
        
    def _error(self, failure):
        log.msg(failure)
        self.sendLine('551 Server error')
            
    def sendLine(self, line):
        log.debug('<-- %r'%line)
        return basic.LineReceiver.sendLine(self, line)
            
    def ftp_USER(self, username):
        if self.state is not self.USER:
            raise 'Bah!'
        self.username = username
        self.state = self.PASS
        self.sendLine('331 User name ok, need pasword')
        
    def ftp_PASS(self, password=None):
        
        def cbLogin((interface, avatar, logout)):
            self.avatar = avatar
            self.logout = logout
            self.state = self.CONNECTED
            self.sendLine('230 User logged in')
            
        def ebLogin(failure):
            failure.trap(error.UnauthorizedLogin)
            self.sendLine('530 Authentication failed')
            self.transport.loseConnection()
            
        if self.state is not self.PASS:
            raise 'Bah!'
        self.password = password
        d = self.factory.login(self.username, self.password)
        d.addCallback(cbLogin)
        d.addErrback(ebLogin)
        return d
        
    def ftp_SYST(self):
        self.sendLine('215 UNIX Type: L8')
        
    def ftp_QUIT(self):
        self.sendLine('221 Logout')
        self.transport.loseConnection()
        
    def ftp_PASV(self):
        # Setup the DTP
        self.dtpFactory = DTPFactory(self.type)
        self.dtpPort = reactor.listenTCP(0, self.dtpFactory)
        # Work out the connection string
        host = tuple(self.transport.getHost().host.split('.'))
        port = divmod(self.dtpPort.socket.getsockname()[1], 256)
        connectTo = ','.join([str(p) for p in host+port])
        # Send it to the client so it can connect
        self.sendLine('227 Entering passive mode (%s)'%connectTo)
        
    def ftp_LIST(self, params=None):
        def writer(protocol, fileInfo):
            stat, thing, user, group, size, date, name = fileInfo
            format = '%s    4 %8s %8s %8d Nov 18 22:00 %s\r\n'
            protocol.write(format%(modeToString(stat),user,group,size,name))
        return self._realList(params, writer)
            
    def _realList(self, params, writer):
        
        # Ignore any arg-like params and extract the optional path
        if params is None:
            params = []
        else:
            params = [p for p in params.split() if p[0] != '-']
        if params:
            path = params[0]
        else:
            path = None
            
        def readyToSend(result):
            self.sendLine('150 Accepted data connection')
            protocol = result[0][1]
            list = result[1][1]
            for fileInfo in list:
                writer(protocol, fileInfo)
            protocol.finish()
            self.sendLine('226 Transfer complete')
            
        d = defer.DeferredList([
            self.dtpFactory.sigConnected,
            defer.maybeDeferred(self.avatar.list, path)
            ])
        d.addCallback(readyToSend)
        d.addErrback(anyFailure)
        return d
        
    def ftp_NLST(self, params=None):
        def writer(protocol, fileInfo):
            protocol.write('%s\r\n'%fileInfo[6])
        return self._realList(params, writer)
        
    def ftp_RETR(self, path=None):
        
        if path is None:
            self.sendLine('501 No file name')
            return

        def error(failure):
            failure.trap(errors.InvalidPath)
            self.sendLine('550 I can only retrieve regular files')
            
        def fileSent(_):
            log.debug('Transfer complete, shutting down DTP')
            self.sendLine('226 Transfer complete')
            
        def gotProducer(producer, protocol):
            producer.consumer = protocol
            protocol.registerProducer(producer, False)
            producer.deferred.addCallback(fileSent)
            producer.deferred.addCallback(self._closeDTP)
            producer.deferred.addErrback(anyFailure)
            self.sendLine('150 Accepted data connection')

        def cbConnected(protocol):
            log.debug('DTP protocol connected, beginning transfer')
            d = defer.maybeDeferred(self.avatar.getFile, path)
            d.addCallback(gotProducer, protocol)
            d.addErrback(error)
        
        self.dtpFactory.sigConnected.addCallback(cbConnected)
        self.dtpFactory.sigConnected.addErrback(anyFailure)
        
    def _closeDTP(self, _):
        self.dtpPort.stopListening()
        self.dtpPort = None
        self.dtpFactory = None
        
    def ftp_STOR(self, path):

        def cbCompleted(f):
            self.sendLine('226 Transfer complete')
        
        def cbConnected(protocol):
            log.debug('DTP protocol connected, accepting upload')
            protocol.consumer = self.avatar.putFile(path)
            protocol.consumer.registerProducer(protocol, True)
            protocol.consumer.deferred.addBoth(cbCompleted)
            self.sendLine('150 accepted data connection')
            
        self.dtpFactory.sigConnected.addCallback(cbConnected)
        self.dtpFactory.sigConnected.addErrback(anyFailure)
        
    def ftp_TYPE(self, type):
        type = type.upper()
        if type == ASCII:
            self.type = ASCII
        elif type == BINARY:
            self.type = BINARY
        else:
            raise 'Bad type'
        self.sendLine('200 TYPE is now "%s"'%self.type)
        
    def ftp_CWD(self, path=None):
        
        def changedDir(dir):
            self.sendLine('250 OK. Current directory is "%s"'%dir)
            
        def error(failure):
            failure.trap(errors.InvalidPath)
            self.sendLine('550 No such directory')
            
        d = defer.maybeDeferred(self.avatar.changeDirectory, path)
        d.addCallback(changedDir)
        d.addErrback(error)
        d.addErrback(anyFailure)
        
    def ftp_PWD(self):
        def gotPWD(pwd):
            self.sendLine('257 "%s" is your current location'%pwd)
        d = defer.maybeDeferred(self.avatar.currentDirectory)
        d.addCallback(gotPWD)
        d.addErrback(anyFailure)
       
    def ftp_SIZE(self, path=None):

        if path is None:
            self.sendLine('500 Missing argument')
            return

        def gotSize(size):
            self.sendLine('213 %d'%size)
            
        def error(failure):
            failure.trap(errors.InvalidPath)
            self.sendLine('550 I can only retrieve regular files')
            
        d = defer.maybeDeferred(self.avatar.getFileSize, path)
        d.addCallback(gotSize)
        d.addErrback(error)
        d.addErrback(anyFailure)
        
    def ftp_MDTM(self, path=None):

        if path is None:
            self.sendLine('500 Missing argument')
            return

        def gotTime(mtime):
            self.sendLine('213 %d'%mtime)

        def error(failure):
            failure.trap(errors.InvalidPath)
            self.sendLine('550 I can only retrieve regular files')
            
        d = defer.maybeDeferred(self.avatar.getFileModificationTime, path)
        d.addCallback(gotTime)
        d.addErrback(error)
        d.addErrback(anyFailure)
        
        
class FTPServerFactory(protocol.ServerFactory):
    protocol = FTPServerProtocol
    
    def __init__(self, portal):
        self.portal = portal

    def login(self, username, password):
        creds = credentials.UsernamePassword(username, password)
        return self.portal.login(creds, None,  iftp.IFTPShell)

            
class DTPProtocol(protocol.Protocol):
    __implements__ = IFinishableConsumer,
    
    producer = None
    consumer = None
    
    def __init__(self, type, sigConnected):
        self.type = type
        self.sigConnected = sigConnected
        self.reset()
        
    def reset(self):
        self.producer = None
        self.consumer = None
    
    def connectionMade(self):
        self.sigConnected.callback(self)
        
    def connectionLost(self, reason):
        if self.consumer is not None:
            self.consumer.finish()
        self.reset()
        
    def dataReceived(self, data):
        self.consumer.write(data)
        
    def registerProducer(self, producer, streaming):
        self.producer = producer
        self.transport.registerProducer(producer, streaming)
        
    def unregisterProducer(self):
        self.producer = None
        self.transport.unregisterProducer()
        
    def write(self, data):
        self.transport.write(data)
        
    def finish(self):
        self.transport.loseConnection()
        
        
class DTPFactory(protocol.ServerFactory):
    
    def __init__(self, type):
        self.type = type
        self.sigConnected = defer.Deferred()
        
    def buildProtocol(self, addr):
        return DTPProtocol(type, self.sigConnected)
        
        
def anyFailure(failure):
    log.debug(failure)
    return failure

    
class SimpleFTPServer(object):

    __implements__ = iftp.IFTPShell

    root = None
    path = '/'
    ignore = '.svn'.split()
    
    def __init__(self, root=None):
        if root is not None:
            self.root = filepath.FilePath(root)
        else:
            self.root = filepath.FilePath(self.root)
        
    def absFilePath(self, *paths):
        path = os.path.normpath(os.path.join(*paths))
        if path.startswith('/'):
            path = path[1:]
        filePath = self.root
        for p in path.split('/'):
            if p in self.ignore:
                raise errors.InvalidPath()
            filePath = filePath.child(p)
        return filePath
        
    def currentDirectory(self):
        return self.path
        
    def changeDirectory(self, path):
        if path is None:
            return
        filePath = self.absFilePath(self.path, path)
        if not filePath.isdir():
            raise errors.InvalidPath()
        newPath = filePath.path[len(self.root.path):]
        self.path = filePath.path[len(self.root.path):] or '/'
        log.msg('Directory changed to "%s"'%self.path)
        return self.path
    
    def list(self, path):

        if path is None:
            path = self.path
        else:
            path = os.path.normpath(os.path.join(self.path, path))

        def gen():
            filePath = self.absFilePath(path)
            for f in filePath.listdir():
                if f in self.ignore:
                    continue
                s = os.stat(filePath.child(f).path)
                yield (
                    s[stat.ST_MODE],
                    'thing',
                    pwd.getpwuid(s[stat.ST_UID])[0],
                    grp.getgrgid(s[stat.ST_GID])[0],
                    s[stat.ST_SIZE],
                    s[stat.ST_MTIME],
                    f
                    )
        return gen()
    
    def getFile(self, path):
        filePath = self.absFilePath(self.path, path)
        if not filePath.isfile():
            raise errors.InvalidPath()
        return ftputil.File(filePath.path)
        
    def getFileSize(self, path):
        filePath = self.absFilePath(self.path, path)
        if not filePath.isfile():
            raise errors.InvalidPath()
        return filePath.getsize()
        
    def getFileModificationTime(self, path):
        filePath = self.absFilePath(self.path, path)
        if not filePath.isfile():
            raise errors.InvalidPath()
        return filePath.getmtime()
        
    def putFile(self, path):
        consumer = ftputil.PutFileConsumer()
        consumer.deferred.addCallback(self.__fileUploaded, path)
        return consumer
        
    def __fileUploaded(self, fsrc, path):
        path = filepath = self.absFilePath(self.path, path).path
        fdst = open(path,'w')
        try:
            shutil.copyfileobj(fsrc, fdst)
        finally:
            fdst.close()
        log.msg('Uploaded to %s' % path)

