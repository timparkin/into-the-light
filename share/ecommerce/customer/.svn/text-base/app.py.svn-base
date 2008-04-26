from zope.interface import implements
from twisted.internet import defer

from tub import itub
from ecommerce.customer import web, manager


class CustomerApplication(object):
    implements(itub.IApplication)

    name = "customer"
    version = 1
    label = "Customers"
    description = "Customers"

    
    def __init__(self, billingCountryFileName=None):
        self.billingCountryFileName = billingCountryFileName

    def setParent(self, parent):
        self.parent = parent

    def initialize(self, realm):
        realm.store.registerType(manager.Customer)

    def getComponents(self):
        return [CustomerComponent(self)]

    def getManager(self):
        return defer.succeed(manager.CustomerManager())

    def getServices(self):
        return self.parent.services

    services = property(getServices)


class CustomerComponent(object):
    implements(itub.IApplicationComponent)

    name = "customer"
    label = "Customers"
    description = "Customer Management"

    def __init__(self, application):
        super(CustomerComponent, self).__init__()
        self.application = application

    def resourceFactory(self, avatar, storeSession, segments):
        return web.CustomerPage(self.application), segments

