import re

from zope.interface import implements
from twisted.python import components
from twisted.internet import defer
from poop import objstore
from pollen.nevow.tabular import itabular, tabular

from cms import icms
from cms.contenttypeutil import storeFile, getFile

from ecommerce.product import index, optionmanager


MISSING = object()

class Product(objstore.Item):
    implements(icms.IAssetDataProvider, icms.IPickableAsset)    
    
    __typename__ = 'ecommerce/product'

    __table__ = 'product'
    title = objstore.column()
    show = objstore.column()
    available = objstore.column()
    categories = objstore.column()
    code = objstore.column()

    _attrs = ('code', 'title', 
        'summary', 'description', 'categories',
        'show', 'available', 'availabilityDescription',
        'date','location','lens','speedaperture','tiltswing','risefall','ndfilters','otherfilters','rating',
        'price','speed','aperture',
        'mainImage',
        'titleTag', 'metaDescription', 'metaKeywords')
    _assetNames = ('mainImage',)

    _stockLevel = 0
    options = []

    pickableAssetNames = ['mainImage']




    def __init__(self, *a, **kw):
        super(Product, self).__init__(*a, **kw)
        self.title = '' # (Sorry!)
        self.speed = ''
        self.aperture = ''
        self.code = ''
        self.show = False
        self.available = False
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
    

    def getPrice(self, option=None):
        if option:
            return optionmanager.getPrice(option)

        elif self.options:
            return optionmanager.getMinimumPrice(self.options)

        return self.price


    def hasPriceRange(self):
        if self.options:
            return optionmanager.hasPriceRange(self.options)
        else:
            return False


    def inStock():
        def getInStock(self):
            if self.options:
                return optionmanager.inStock(self.options)
            else:
                return self._stockLevel > 0

        return property(getInStock)
    inStock = inStock()


    def getStockLevel(self):
        return self._stockLevel


    def initialiseStockLevels(self, stockLevels):
        """This is used by the manager to set read only stock levels on a product.
           To manage stock levels use a StockManager."""
        for stock in stockLevels:
            option_code = stock['option_code']
            level = stock['level']

            if not option_code:
                self._stockLevel = level
            else:
                for option in self.options:
                    if option['code'] == option_code:
                        option['_stockLevel'] = level
                        break

    
    def hasOptions(self):
        return self.options != []


    def getInStockOptions(self):
        return optionmanager.getInStockOptions(self.options)


    def getOption(self, optionCode):
        for option in self.options:
            if option['code'] == optionCode:
                return option
        return None

from cms.contentitem import NonPagishPluginBase
class ProductPlugin(NonPagishPluginBase):

    name = 'Photo'
    contentItemClass = Product
    description = 'Photo'
    id = 'ecommerce/photo'



class ProductTabularItem(object):
    implements(itabular.IItem)

    def __init__(self, product):
        self.product = product

    def getAttributeValue(self, name):
        if name.startswith('category-'):
            category = '.'.join(name[9:].split('1234567890'))
            if self.product.categories is None:
                return False
            if category in self.product.categories:
                return True
            else:
                return False
        return getattr(self.product, name)

components.registerAdapter(ProductTabularItem, Product, itabular.IItem)


@defer.deferredGenerator
def storeAssets(storeSession, assetNames, original, data):


    for assetName in assetNames:

        fileId = getattr(original, assetName, None)
        if data.get(assetName) is None:
            data[assetName] = fileId
        elif data.get(assetName) == (None,None,None):
            data[assetName] = None
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



class ProductTabularModel(tabular.SequenceListModel):
    pass


class ProductManager(object):

    def __init__(self, indexer=None, stockManager=None, optionManager=None):
        self.indexer = indexer
        if self.indexer is None:
            self.indexer = index.NullProductIndexer()
        self.stockManager = stockManager
        self.optionManager = optionManager


    def hasStockManager(self):
        return self.stockManager is not None


    def getStockManager(self):
        return self.stockManager


    def hasOptionManager(self):
        return self.optionManager is not None


    def getOptionManager(self):
        return self.optionManager


    def findById(self, storeSession, id):
        d = storeSession.getItemById(id)
        d.addCallback(self._getStockLevel, storeSession)
        return d
    
    def findManyByIds(self,storeSession,ids):
        return storeSession.getItems(itemType=Product, where=where)

        

    def findMany(self, storeSession, where=None, params=None, keyWords=None, priceRange=None):

        def idsWhere(ids):
            where = ', '.join([str(id) for id in ids])
            return ' (product.id in (' + where + ')) '

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
                return storeSession.getItems(itemType=Product, where=where,
                    params=params, orderBy='title')


        def filterByPriceRange(items, priceRange):
            lowerBound = int(priceRange[0])
            upperBound = int(priceRange[1])
            for item in items:
                price = item.getPrice()
                if price >= lowerBound and price <=upperBound:
                    yield item

        if keyWords:
            #print 'trying indexer with %s'%keyWords
            d = self.indexer.getMatchingIds(keyWords)
        else:
            #print 'no keywords'
            d = defer.succeed(None)

        d.addCallback(addIdsToWhere, where, params)
        d.addCallback(getItems)
        if priceRange is not None:
            d.addCallback(filterByPriceRange,priceRange)
        d.addCallback(self._getStockLevels, storeSession)
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


        def addToIndex(product):
            d = self.indexer.add(product)
            d.addCallback(lambda ignore: product)
            return d


        d = storeSession.createItem(Product)
        d.addCallback(flush, storeSession)
        d.addCallback(addToIndex)
        d.addCallback(self.update, data, storeSession)
        return d


    def update(self, product, data, storeSession):


        def storeAttrs(product, data):
            for attr in product._attrs:
                value = data.get(attr, MISSING)
                if value != MISSING:
                    setattr(product, attr, value)


        def updateIndex(product):
            return self.indexer.update(product)

        product.touch()

        d = storeAssets(storeSession, product._assetNames, product, data)
        d.addCallback(lambda ignore: storeAttrs(product, data))
        d.addCallback(lambda ignore: product)
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
                where.append( 'product.categories <@ %%(%s)s'%paramKey )
                params[paramKey] = cat


        where = []
        params = {}

        categories = criteria.get('categories')
        if categories:
            addCategoriesClause(categories, where, params)

        title = criteria.get('title')
        if title:
            addStringClause('product.title', title, where, params)

        keyWords = criteria.get('keyWords')
        if where == []:
            where = None
            params = None

        d = defer.succeed(None)
        d.addCallback(lambda ids: self.findMany(storeSession, where, params, keyWords=keyWords))
        d.addCallback(lambda products: ProductTabularModel(list(products))) 
        return d


    def _getStockLevel(self, item, storeSession):
        if item is None:
            return defer.succeed(None)

        d = self._getStockLevels([item], storeSession)
        d.addCallback(lambda items: items[0])
        return d


    def _getStockLevels(self, items, storeSession):
        items = (items and list(items)) or []

        # No stock manager or no items
        if self.stockManager is None or not items:
            return defer.succeed(items)


        def gotLevels(stockLevels):
            for item in items:
                levels = stockLevels[item.id]

                item.initialiseStockLevels(levels)

            return items

        ids = [item.id for item in items]
        d = self.stockManager.getCurrentLevels(storeSession, ids)
        d.addCallback(gotLevels)
        return d



def debug(r, mess):
    print '>>DEBUG', mess, r
    return r
