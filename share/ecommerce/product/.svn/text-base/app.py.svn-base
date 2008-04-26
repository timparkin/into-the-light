from zope.interface import implements
from twisted.internet import defer

from tub import itub
from ecommerce.product import web, manager


class ProductApplication(object):
    implements(itub.IApplication)

    name = "product"
    version = 1
    label = "Photos"
    description = "Product Management"

    def __init__(self, assetServiceName, indexer, stockManager=None, optionManager=None, restWriter=None):
        self.assetServiceName = assetServiceName
        self.indexer = indexer
        self.stockManager = stockManager
        self.restWriter = restWriter
        self.optionManager = optionManager

    def setParent(self, parent):
        self.parent = parent

    def initialize(self, realm):
        realm.store.registerType(manager.Product)

    def getComponents(self):
        return [ProductComponent(self)]

    def getManager(self):
        return defer.succeed(manager.ProductManager(self.indexer, self.stockManager, self.optionManager))

    def getServices(self):
        return self.parent.services

    services = property(getServices)


class ProductComponent(object):
    implements(itub.IApplicationComponent)

    name = "photos"
    label = "Photos"
    description = "Product Management"

    def __init__(self, application):
        super(ProductComponent, self).__init__()
        self.application = application

    def resourceFactory(self, avatar, storeSession, segments):
        return web.ProductPage(self.application), segments

