import os
import os.path
import shutil
from twisted.internet import reactor, defer
import purepg.adbapi
from tub import store as tub_store

from ecommerce.product.manager import Product



def rebuildIndex(storeSession, indexer):

    attrNames = ['id', 'version', 'type', 'ctime', 'mtime', 'olcount', 'attrs']

    @defer.deferredGenerator
    def gotItems(rows):

        for row in rows:
            id, version, type, ctime, mtime, olcount, attrs = row

            product = storeSession.reconstituteItem(dict(zip(attrNames,
                              [id, version, type, ctime, mtime, olcount, attrs])))

            print "Indexing product", product
            d = indexer.update(product)
            d = defer.waitForDeferred(d)
            yield d
            d.getResult()


    sql = """
        select %(attrs)s
        from item 
        where
            type = 'ecommerce/product'"""

    params = { 'attrs': ', '.join(attrNames) }

    d = storeSession.curs.execute(sql%params)
    d.addCallback(lambda ignore: storeSession.curs.fetchall())
    d.addCallback(gotItems)
    return d

def debug(r, mess):
    print '>> DEBUG', mess, r
    return r



def buildOptionParser():
    from optparse import OptionParser

    parser = OptionParser()

    parser.add_option("-c", "--config", dest="config", 
        help="config e.g: config.yaml")
    parser.add_option("-a", "--admin", dest="admin", 
        help="Directory to write the admin index.")
    parser.add_option("-p", "--public", dest="public", 
        help="Directory to write the public index.")

    return parser



def switchDirectories(real, new, tmp):
    """Switch between the new and existing index directories, using the tmp as required"""
    try:
        print 'Renaming %s to %s'%(real, tmp)
        if os.path.exists(real):
            os.rename(real, tmp)
    except:         
        raise

    try:
        print 'Renaming %s to %s'%(new, real)
        os.rename(new, real)
    except:
        try:
            if os.path.exists(tmp):
                os.rename(tmp, real)
        except:
            raise
        raise

    if os.path.exists(tmp):
        print 'Deleting %s'%tmp
        shutil.rmtree(tmp)



if __name__ == '__main__':
    import sys
    from twisted.internet import reactor

    parser = buildOptionParser()

    (options, args) = parser.parse_args()

    print options
    print args

    if options.config is None or options.admin is None or options.public is None:
        print 'Must specify all of config, admin directory and public directory'
        sys.exit(1)

    # Load the configuration file
    import syck
    config = syck.load(open(options.config))
    connectionPool = purepg.adbapi.ConnectionPool(**config['database']['args'])
    store = tub_store.TubStore(connectionPool.connect)
    store.registerType(Product)

    tmpAdminDir = options.admin + '.tmp'
    tmpPublicDir = options.public + '.tmp'
    newAdminDir = options.admin + '.new'
    newPublicDir = options.public + '.new'

    if os.path.exists(newAdminDir) or os.path.exists(tmpAdminDir) \
        or os.path.exists(newPublicDir) or os.path.exists(tmpPublicDir):

        print '%s or %s or %s or %s directories already exists'%(newAdminDir, tmpAdminDir, newPublicDir, tmpPublicDir)
        sys.exit(1)

    from services import indexing
    indexer = indexing.ProductIndexer(newAdminDir, newPublicDir, config['indexes']['dontIndexCategory'])

    d = store.startSession()
    d.addCallback(rebuildIndex, indexer)
    d.addCallback(lambda ignore: switchDirectories(options.admin, newAdminDir, tmpAdminDir))
    d.addCallback(lambda ignore: switchDirectories(options.public, newPublicDir, tmpPublicDir))
    d.addBoth(debug, 'at end')
    d.addBoth(lambda ignore: reactor.stop())
    

    reactor.run()

