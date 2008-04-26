import optparse
import sys
from twisted.internet import reactor, defer
from twisted.python import reflect
from poop import objstore
from purepg import adbapi

exitCode = 0

def makeStore(**kw):
    """
    Create an object store.
    """
    def connectionFactory():
        return adbapi.connect(**kw)
    return objstore.ObjectStore(connectionFactory)
    
@defer.inlineCallbacks
def createItem(session, type, args, attrs):
    """
    Create the item with the given type and attrs.
    """
    item = yield session.createItem(type, **args)
    for k,v in attrs.items():
        setattr(item,k,v)
    item.touch()
    yield defer.returnValue( item )
    

def itemCreated(item):
    """
    Print the item
    """
    global exitCode
    exitCode = 0
    print 'New %r item added, id=%d' % (item.__class__.__name__, item.id)
    
def error(failure):
    """
    Print the failure.
    """
    global exitCode
    exitCode = 1
    failure.printBriefTraceback()
    
def main():
    
    # Setup the option parser
    parser = optparse.OptionParser()
    parser.add_option('-d', '--database', type="string", dest='database', help='database name')
    parser.add_option('-u', '--user', type="string", dest='user', help='database user')
    parser.add_option('-t', '--type', type="string", dest='type', help='item type')
    parser.add_option('-e', '--execfile', type="string", dest='execfile', help='code to exec to get attrs')
    

    # Parse the command line options
    (options, args) = parser.parse_args()
    
    if options.database is None or options.type is None:
        parser.print_help()
        return -1

    # Extract the item type and turn the positional args into a dict of attrs
    type = reflect.namedClass(options.type)
    args = dict(arg.split('=', 1) for arg in args)
    g = {}
    execfile(options.execfile,g)
    attrs=g['attrs']
    # Create the object store
    store = makeStore(database=options.database, user=options.user)
    
    # Add the item and shutdown the reactor when it's complete
    d = store.runInSession(createItem, type, args, attrs)
    d.addCallbacks(itemCreated, error)
    d.addBoth(lambda ignore: reactor.stop())
    
    # Off we go
    reactor.run()
    sys.exit(exitCode)


if __name__ == '__main__':
    main()

