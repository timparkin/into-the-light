from zope.interface import implements
from twisted.internet import defer

from tub import itub
from ecommerce.delivery import web, manager


class DeliveryChargeApplication(object):
    implements(itub.IApplication)

    name = "delivery"
    version = 1
    label = "Delivery Charge Management"
    description = "Delivery Charge Management"

    
    def __init__(self, countryCodeFileName=None):
        self.countryCodeFileName = countryCodeFileName

    def setParent(self, parent):
        self.parent = parent

    def initialize(self, realm):
        realm.store.registerType(manager.DeliveryCharge)

    def getComponents(self):
        return [DeliveryChargeComponent(self)]

    def getManager(self):
        return defer.succeed(manager.DeliveryChargeManager())

    def getServices(self):
        return self.parent.services

    services = property(getServices)


class DeliveryChargeComponent(object):
    implements(itub.IApplicationComponent)

    name = "delivery"
    label = "Delivery Charge Management"
    description = "Delivery Charge Management"

    def __init__(self, application):
        super(DeliveryChargeComponent, self).__init__()
        self.application = application

    def resourceFactory(self, avatar, storeSession, segments):
        return web.DeliveryChargePage(self.application), segments

