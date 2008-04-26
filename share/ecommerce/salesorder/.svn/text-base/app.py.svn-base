from twisted.internet import defer
from zope.interface import implements
from tub import itub
from ecommerce.salesorder import web, manager

class SalesOrderApplication(object):
    implements(itub.IApplication)

    name = "salesorder"
    version = 1
    label = "Enquiries"
    description = "Sales Orders from the site"

    def __init__(self, config, htmlEmailFactory=None):
        self.config = config
        self.htmlEmailFactory = htmlEmailFactory


    def initialize(self, realm):
        pass


    def getComponents(self):
        return [
            SalesOrderComponent(self),
            ]


    def getManager(self):
        return manager.SalesOrderManager(self.config)


    def setParent(self, parent):
        self.parent = parent



class SalesOrderComponent(object):
    implements(itub.IApplicationComponent)

    name = "salesorder"
    label = "Enquiries"
    description = "Sales Order Management"

    def __init__(self, app):
        self.app = app

    def resourceFactory(self, avatar, storeSession, segments):
        return web.SalesOrdersPage(avatar, self.app), segments
