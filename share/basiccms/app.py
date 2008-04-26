from twisted.python import components, log, reflect
from nevow import inevow
from tub.public import app
from notification import inotification
from static_data import app as static_data_app

from basiccms.cmsnotification import NotificationService

from ecommerce.product.manager import Product, ProductManager
from ecommerce.product.optionmanager import OptionManager
from ecommerce.salesorder.manager import SalesOrderManager

from comments.model import Comment
from comments.service import CommentsService

from basiccms import basket
from basiccms.web import overlay
from services import indexing


def registerAdapters(adapters):
    for a, o, i in adapters:
        log.msg('Registering adapter: %s, %s, %s' % (a,o,i))
        a, o, i = map(reflect.namedAny, [a, o, i])
        components.registerAdapter(a, o, i)


class Realm(app.Realm):



    def __init__(self, *a, **k):
        anonymousResourceFactory = k.pop('anonymousResourceFactory', None)
        super(Realm, self).__init__(*a, **k)
        registerAdapters(self.config['adapters'])
        self.notificationService = NotificationService(**self.config['notification'])
        self.staticData = static_data_app.StaticData(self.config['staticData']['baseDir'], **self.config['staticData']['files'])
        if anonymousResourceFactory is not None:
            self.anonymousResourceFactory = anonymousResourceFactory

        indexer = indexing.PublicProductIndexer(self.config['indexes']['product'],
            self.config['indexes']['dontIndexCategory'])
        self.products = ProductManager(indexer, None, OptionManager()) 
        self.commentsService = CommentsService()  
        self.store.registerType(Comment)  
        self._salesOrders = None
        

    def anonymousAvatarFactory(self):
        return Avatar(self)



    def anonymousResourceFactory(self, avatar):
        """
        Create a basic (unwrapped) resource for the given avatar.
        """
        from basiccms.web import root
        return root.RootResource(avatar)

    def getSalesOrders(self):
        if self._salesOrders is None:
            self._salesOrders = SalesOrderManager(self.config['ecommerce'])
        return self._salesOrders

    salesOrders = property(getSalesOrders)

components.registerAdapter(lambda realm: realm.notificationService, Realm, inotification.INotificationService)


def wrapRootResource(resource, avatar):
    """
    Wrap a root resource, normally an instance of a resource class adapted from
    the avatar, with a standard wrapers:

       * Not Found -- catches 404s and displays a nice page using a named
         template.
       * Transaction -- process the whole request in a single database
         transaction

    This function make setting up the root resource easier (and more
    maintainable!) if you ever need to replace the avatar->resource adaption
    process.
    """
    from pollen.nevow import wrappers
    from tub.web.wrappers import TransactionalResourceWrapper
    from basiccms.web import root
    resource = wrappers.NotFoundWrapper(resource, root.notFoundResourceFactory)
    resource = TransactionalResourceWrapper(resource, avatar)
    return resource


class Avatar(app.AnonymousAvatar):


    def __init__(self, *a, **k):
        super(Avatar, self).__init__(*a, **k)
        self.basket = basket.Basket(self)
        self.checkoutDetails = None


    def getProducts(self, storeSession, categorisationFilters=None, keyWords=None, priceRange=None):

        def gotProducts(products):
            products.sort(lambda f,s: -cmp(f.rating, s.rating))
            return products
        # Only showing products
        where = ["show = %(show)s"]
        params = {'show': True}
        # Apply categorisation filters
        if categorisationFilters:
            for i, (facet, category) in enumerate(categorisationFilters):
                param = 'catfilter%d' % i
                where.append('%%(%s)s ~ categories' % param)
                params[param] = '%s.*.%s' % (facet, category)
        # Find the products
        d = self.realm.products.findMany(storeSession, where=where,
                params=params, keyWords=keyWords, priceRange=priceRange)
        d.addCallback(gotProducts)
        return d

    
    def getProduct(self, storeSession, id):
        d = self.realm.products.findById(storeSession, id)
        def checkShowing(product):
            if product.show:
                return product
            return None
        d.addCallback(checkShowing)
        return d

    def getProductByCode(self,storeSession, code):
        
        # Only showing products
        where = ["show = %(show)s","code = %(code)s"]
        params = {'show': True, 'code': code}
        # Find the products
        d = self.realm.products.findMany(storeSession, where=where,
                params=params)
        d.addCallback(lambda many: many and many[0] or None)
        return d


    def getCustomerByEmail(self, storeSession, email):

        def oneOrNone(customers):
            customers = list(customers)
            if len(customers) > 0:
                return customers[0]
            return None

        where = [ 'customer.email = %(email)s' ]
        params = { 'email': email }

        d = self.realm.customers.findMany(storeSession, where=where, params=params)
        d.addCallback(oneOrNone)
        return d


def avatarResourceFactory(avatar):
    """
    Call the realm to create a basic, root resource for the avatar and then
    wrap the avatar's resource in the standard resource wrappers.
    """
    resource = avatar.realm.anonymousResourceFactory(avatar)
    return wrapRootResource(resource, avatar)


components.registerAdapter(avatarResourceFactory, app.AnonymousAvatar, inevow.IResource)

