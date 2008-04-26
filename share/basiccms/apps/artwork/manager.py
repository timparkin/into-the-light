import re

from zope.interface import implements
from twisted.python import components
from twisted.internet import defer
from poop import objstore
from pollen.nevow.tabular import itabular, tabular

from cms import icms
from cms.contenttypeutil import storeFile, getFile

from basiccms.apps.artwork import index


class Artwork(objstore.Item):
    implements(icms.IAssetDataProvider)
    
    __typename__ = 'basiccms/artwork'

    __table__ = 'artwork'
    title = objstore.column()
    show = objstore.column()
    available = objstore.column()
    categories = objstore.column()

    _attrs = ('title', 'longTitle',
        'shortDescription', 'description', 'categories',
        'show', 'available',
        'price',
        'mainImage', 
        'titleTag', 'metaDescription', 'metaKeywords')

    _assetNames = ('mainImage')

    def __init__(self, *a, **kw):
        super(Artwork, self).__init__(*a, **kw)
        self.title = '' # (Sorry!)
        self.show = True
        self.available = True
        self.categories = []

    def provideData(self, avatar, storeSession, assetName, langs):

        # Get data from external table
        if assetName is None:
            raise KeyError()
        fileId = getattr(self, assetName, None)
        if not fileId:
            raise KeyError()

        d = getFile(storeSession, fileId)
        d.addCallback(lambda data: data[:2])
        return d

class ArtworkTabularItem(object):
    implements(itabular.IItem)

    def __init__(self, artwork):
        self.artwork = artwork

    def getAttributeValue(self, name):
        return getattr(self.artwork, name)

components.registerAdapter(ArtworkTabularItem, Artwork, itabular.IItem)

@defer.deferredGenerator
def storeAssets(storeSession, assetNames, original, data):

    for assetName in assetNames:
        
        fileId = getattr(original, assetName, None)
        if data.get(assetName) is None:
            data[assetName] = fileId
        else:
            # Store data in external table
            d = storeFile(storeSession, fileId,
                original.id, original.version,
                assetName, data[assetName])
            d = defer.waitForDeferred(d)
            yield d
            fileId = d.getResult()
            data[assetName] = fileId

        yield data

class ArtworkTabularModel(tabular.SequenceListModel):
    pass


class ArtworkManager(object):

    def __init__(self, indexer=None):
        self.indexer = indexer
        if self.indexer is None:
            self.indexer = index.NullArtworkIndexer()

    def findById(self, storeSession, id):
        return storeSession.getItemById(id)

    def findMany(self, storeSession, where=None, params=None, keyWords=None):

        def idsWhere(ids):
            where = ', '.join([str(id) for id in ids])
            return ' (artwork.id in (' + where + ')) '

        def addIdsToWhere(ids, where, params):
            if ids == []: # No matching ids
                return (False, where, params)
            if ids is None: # No restrictions on ids
                return (True, where, params)

            if where:
                where.append( idsWhere(ids) )
            else:
                where = [idsWhere(ids)]

            return (True, where, params)

        def getItems(criteria):
            runQuery, where, params = criteria

            if where:
                where = ' and '.join( where )

            if not runQuery:
                return defer.succeed([])
            else:
                return storeSession.getItems(itemType=Artwork, where=where,
                    params=params, orderBy='title')

        if keyWords:
            d = self.indexer.getMatchingIds(keyWords)
        else:
            d = defer.succeed(None)

        d.addCallback(addIdsToWhere, where, params)
        d.addCallback(getItems)
        return d


    def remove(self, storeSession, id):
        def removeFromIndex(ignore):
            return self.indexer.remove(id)

        d = storeSession.removeItem(id)
        d.addCallback(removeFromIndex)
        return d

    def create(self, storeSession, data):

        def flush(item, sess):
            d = sess.flush()
            d.addCallback(lambda ignore: item)
            return d

        def addToIndex(artwork):
            d = self.indexer.add(artwork, storeSession)
            d.addCallback(lambda ignore: artwork)
            return d

        d = storeSession.createItem(Artwork)
        d.addCallback(flush, storeSession)
        d.addCallback(addToIndex)
        d.addCallback(self.update, data, storeSession)

        return d

    def update(self, item, data, storeSession):

        def storeAttrs(ignore):
            for attr in item._attrs:
                value = data.get(attr, None)
                setattr(item, attr, value)

        def updateIndex(artwork):
            return self.indexer.update(artwork, storeSession)

        item.touch()

        d = storeAssets(storeSession, item._assetNames, item, data)
        d.addCallback(storeAttrs)
        d.addCallback(lambda ignore: item)
        d.addCallback(updateIndex)
        return d

    def getTabularModel(self, storeSession, criteria):

        class ParamKey(object):
            def __init__(self):
                self.number = 0

            def __call__(self):
                self.number = self.number + 1
                return 'param_%s'%self.number

        getParamNextKey = ParamKey()

        def addStringClause(column, value, where, params):
            paramKey = getParamNextKey()
            
            where.append( ' %s like %%(%s)s '%(column, paramKey) )
            params[paramKey] = value.replace('*', '%')

        def addCategoriesClause(categories, where, params):

            for cat in categories:
                paramKey = getParamNextKey()
                where.append( 'artwork.categories ~ %%(%s)s'%paramKey )
                params[paramKey] = cat


        where = []
        params = {}

        categories = criteria.get('categories')
        if categories:
            addCategoriesClause(categories, where, params)

        title = criteria.get('title')
        if title:
            addStringClause('artwork.title', title, where, params)

        keyWords = criteria.get('keyWords')
        if where == []:
            where = None
            params = None

        d = defer.succeed(None)
        d.addCallback(lambda ids: self.findMany(storeSession, where, params, keyWords=keyWords))
        d.addCallback(lambda artworks: ArtworkTabularModel(list(artworks))) 
        return d


