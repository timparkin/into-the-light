from zope.interface import implements, Interface
from twisted.internet import defer
from twisted.python import log
from nevow import inevow
from poop import store
from pollen.nevow import wrappers

from tub.web import util


        
class TransactionalResourceWrapper(wrappers.FinalResourceWrapper):
    """
    A wrapper that allows all storage actions during a request to be part of a
    single transaction. If the request completes successfully then the session
    is committed; if the request fails then the session is discarded.
    """
    
    def __init__(self, resource, avatar):
        super(TransactionalResourceWrapper, self).__init__(resource, avatar)
        self.avatar = avatar
    
    def locateChild(self, ctx, segments):
        d = self.openStoreSession(ctx)
        d.addCallback(lambda ignore: super(TransactionalResourceWrapper, self).locateChild(ctx, segments))
        return d
    
    def renderHTTP(self, ctx):
        d = self.openStoreSession(ctx)
        d.addCallback(lambda ignore: super(TransactionalResourceWrapper, self).renderHTTP(ctx))
        return d
        
    def openStoreSession(self, ctx):
        request = inevow.IRequest(ctx)
        storeSession = request.getComponent(store.IStoreSession)
        if storeSession is not None:
            return defer.succeed(None)
        def storeSessionStarted(storeSession):
            self.log(ctx, 'Starting store session (%s)' % inevow.IRequest(ctx).uri)
            request.setComponent(store.IStoreSession, storeSession)
            storeSession.initCapCtx(self.avatar)
            return None
        d = self.avatar.realm.store.startSession()
        d.addCallback(storeSessionStarted)
        return d
        
    def log(self, ctx, msg, *a, **k):
        return
        msg = '%d -- %s' % (id(inevow.IRequest(ctx)), msg)
        log.write(msg, *a, **k)
    
    def success(self, result, ctx):
        d = self.commit(ctx)
        d.addBoth(self.closeSession, ctx)
        d.addCallback(lambda ignore: result)
        return d
        
    def error(self, failure, ctx):
        d = self.rollback(ctx)
        d.addBoth(self.closeSession, ctx)
        d.addCallback(lambda ignore: failure)
        return d

    def notFound(self, ctx):
        d = self.rollback(ctx)
        d.addBoth(self.closeSession, ctx)
        d.addCallback(lambda ignore: None)
        return d
        
    def closeSession(self, result, ctx):
        self.log(ctx, 'Closing store session')
        storeSession = self.locateStoreSession(ctx)
        if storeSession is None:
            return defer.succeed(result)
        d = storeSession.close()
        d.addCallback(lambda ignore: result)
        return d
        
    def commit(self, ctx):
        session = self.locateStoreSession(ctx)
        if session is None:
            return defer.succeed(None)
        if session.forceRollback:
            self.log(ctx, 'Forcing store session rollback')
            return session.rollback()
        else:
            self.log(ctx, 'Committing store session')
            return session.commit()

    def rollback(self, ctx):
        session = self.locateStoreSession(ctx)
        if session is None:
            return defer.succeed(None)
        self.log(ctx, 'Rolling back store session')
        return session.rollback()
        
    def locateStoreSession(self, ctx):
        request = inevow.IRequest(ctx)
        session = request.getComponent(store.IStoreSession)
        return session



class SkinSetupResourceWrapper(wrappers.SeeThroughWrapper):

    implements(inevow.IResource)

    def __init__(self, wrapped, defaultSkin):
        wrappers.SeeThroughWrapper.__init__(self, wrapped)
        self.defaultSkin = defaultSkin

    def locateChild(self, ctx, segments):
        return util.appendSkinsAndCall(ctx, [self.defaultSkin], self.wrapped.locateChild, ctx, segments)

    def renderHTTP(self, ctx):
        return util.appendSkinsAndCall(ctx, [self.defaultSkin], self.wrapped.renderHTTP, ctx)

