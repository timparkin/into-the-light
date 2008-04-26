"""
laxdb - unblocks the parts other database modules leave blocked.

laxdb is an experimental, untested, incomplete (although probably complete
enough) attempt at wrapping a blocking DB-API module (psycopg, pyPgSQL, etc)
in something that feels more async than Twisted's adbapi.

The module also contains a connection pool implementation.

An example of using laxdb is:

    def connected(conn):
        curs = conn.cursor()
        d = curs.execute("select * from test")
        d.addCallback(lambda ignore: curs.fetchall())
        d.addCallback(lambda rows: pprint(rows))
        d.addCallback(lambda ignore: curs.close())
        d.addCallback(lambda ignore: conn.close())
    conn = laxdb.connect('psycopg', database='test')

None of those calls block. laxdb dispatches all blocking calls to a dedicated
worker thread and fires the deferred when the dispatched call completes.

It has a couple of advantages over adbapi:

    * A more natural (although async) API.
    * Calls to other systems can be interleaved with calls to the database when
      necessary; all calls to the database can be kept to one transaction.

AFAICT, the number of threads required is no greater than adbapi and, in some
ways, laxdb is more controllable.

The amount of thread context switching may hurt laxdb performance.
"""

import threading, Queue
from twisted.application import service
from twisted.internet import defer, reactor
from twisted.python import failure, log, reflect, threadable


# initialize threading
threadable.init(1)


def connect(dbapi, *args, **kwargs):
    """Asychronously connect to a database using the given dbapi module.
    """
    def connected(conn, worker):
        return Connection(conn, worker)
    dbapi = getattr(reflect.namedAny(dbapi), 'connect')
    worker = WorkerThread()
    d = worker.dispatch(dbapi, *args, **kwargs)
    d.addCallback(connected, worker)
    return d


class ConnectionPool(object):

    minSize = 3
    maxSize = 10

    def __init__(self, *a, **k):
        self._args = a
        self._kwargs = k
        self._available = []
        self._inuse = []
        self._waiting = []
        self._connecting = 0
        self._closingDeferred = None

    def close(self):
        if self._canClose():
            d = defer.succeed(None)
        else:
            d = self._closingDeferred = defer.Deferred()
        d.addCallback(self._cbClose)
        return d

    def connect(self):
        assert self._closingDeferred is None
        try:
            conn = self._available.pop()
        except IndexError:
            conn = None

        if conn is not None:
            # For convenience, wrap in a succeeding deferred
            d = defer.succeed(conn)
        else:
            # Allocate a new connection or add the caller to the waiting list
            if len(self._inuse)+self._connecting < self.maxSize:
                self._connecting += 1
                d = connect(*self._args, **self._kwargs)
                def decConnecting(result):
                    self._connecting -= 1
                    return result
                d.addBoth(decConnecting)
            else:
                d = defer.Deferred()
                self._waiting.append(d)

        d.addCallback(self._cbConnected)
        return d

    def logStats(self):
        log.msg('available=%d, connecting=%d, inuse=%d, waiting=%d' % (len(self._available), self._connecting, len(self._inuse), len(self._waiting)))

    def _cbClose(self, spam):
        available = self._available[:]
        d = defer.DeferredList([conn.close() for conn in available])
        return d

    def _canClose(self):
        return not self._inuse and not self._waiting

    def _cbConnected(self, conn):
        self._inuse.append(conn)
        return PooledConnection(self, conn)

    def _connectionClosed(self, conn):
        # We want the real connection, not the pooled wrapper
        conn = conn._conn
        # Rollback the transaction before it gets used again
        d = conn.rollback()
        d.addCallback(self._cbConnectionReady, conn)
        d.addErrback(self._cbConnectionClosedFailed, conn)
        return d

    def _cbConnectionClosedFailed(self, failure, conn):
        self._inuse.remove(conn)
        d = conn.close()
        return d

    def _cbConnectionReady(self, spam, conn):
        # Remove from the inuse list
        self._inuse.remove(conn)

        if self._waiting:
            d = self._waiting.pop(0)
            d.callback(conn)
            d = defer.succeed(None)
        else:
            if len(self._available)+len(self._inuse) >= self.minSize:
                d = conn.close()
            else:
                self._available.append(conn)
                d = defer.succeed(None)
        # If we're waiting to close and there is nothing left to run then
        # fire the closing deferred.
        if self._closingDeferred is not None and self._canClose():
            self._closingDeferred.callback(None)
        return d


class ConnectionPoolService(service.Service):

    def __init__(self, pool):
        self._pool = pool

    def stopService(self):
        d = self._pool.close()
        d.addCallback(lambda spam: service.Service.stopService(self))
        return d


class PooledConnection(object):

    def __init__(self, pool, conn):
        self._pool = pool
        self._conn = conn
        self._closed = False

    def __del__(self):
        if not self._closed:
            self.close()

    def close(self):
        self._closed = True
        return self._pool._connectionClosed(self)

    def __getattr__(self, name):
        return getattr(self._conn, name)


class Connection(object):
    """A non-blocking database connection wrapper.
    """

    def __init__(self, conn, worker):
        self._conn = conn
        self._worker = worker

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def close(self):
        d = self._worker.dispatch(self._conn.close)
        d.addCallback(lambda r: self._worker.shutdown())
        return d

    def commit(self):
        return self._worker.dispatch(self._conn.commit)

    def rollback(self):
        return self._worker.dispatch(self._conn.rollback)

    def cursor(self):
        return Cursor(self._conn.cursor(), self, self._worker)


class Cursor(object):
    """A non-blocking cursor.
    """

    def __init__(self, curs, conn, worker):
        self._curs = curs
        self._conn = conn
        self._worker = worker

    def __getattr__(self, name):
        return getattr(self._curs, name)

    def callproc(self, *a, **kw):
        return self._worker.dispatch(self._curs.callproc, *a, **kw)

    def execute(self, *a, **kw):
        return self._worker.dispatch(self._curs.execute, *a, **kw)

    def executemany(self, *a, **kw):
        return self._worker.dispatch(self._curs.executemany, *a, **kw)

    def fetchone(self, *a, **kw):
        return self._worker.dispatch(self._curs.fetchone, *a, **kw)

    def fetchmany(self, *a, **kw):
        return self._worker.dispatch(self._curs.fetchmany, *a, **kw)

    def fetchall(self, *a, **kw):
        return self._worker.dispatch(self._curs.fetchall, *a, **kw)

    def nextset(self, *a, **kw):
        return self._worker.dispatch(self._curs.nextset, *a, **kw)

    def close(self, *a, **kw):
        pass


class WorkerThread(object):
    """Worker thread.
    """

    # SHUTDOWN object. This is put in the queue to cleanly close the thread.
    SHUTDOWN = object()

    _thread = None
    _shutdownTriggerId = None

    def __init__(self):
        self._q = Queue.Queue()

    def dispatch(self, func, *a, **k):
        """Dispatch the function and arguments to the thread and return a
        Deferred that will fire with the result or error.
        """
        if self._thread is None:
            self._start()
        d = defer.Deferred()
        self._q.put( (d, func, a, k) )
        return d

    def shutdown(self):
        """Shutdown the worker thread.
        """
        self._q.put(self.SHUTDOWN)
        if self._shutdownTriggerId is not None:
            reactor.removeSystemEventTrigger(self._shutdownTriggerId)
            self._shutdownTriggerId = None

    def _start(self):
        """Start the worker thread.
        """
        self._thread = threading.Thread(target=self._worker)
        self._thread.start()
        self._shutdownTriggerId = reactor.addSystemEventTrigger('after', 'shutdown', self.shutdown)

    def _worker(self):
        """Worker thread function.
        """

        def scopeSafeCallable(func, value):
            def sender():
                func(value)
            return sender

        while True:
            o = self._q.get()
            if o is self.SHUTDOWN:
                break
            d, func, args, kwargs = o
            try:
                result = func(*args, **kwargs)
            except:
                import sys
                type, value, traceback = sys.exc_info()
                reactor.callFromThread(scopeSafeCallable(d.errback, failure.Failure(value, type, traceback)))
            else:
                reactor.callFromThread(scopeSafeCallable(d.callback, result))


__all__ = ['connect', 'ConnectionPool', 'ConnectionPoolService']
