from zope.interface import implements
from nevow import url

from tub import itub

from cms import systemservices
from ecommerce import web
from ecommerce.product import assetbrowser

class ECommerceApplication(object):
    implements(itub.IApplication)

    name = "ecommerce"
    version = 1
    label = "E-Commerce"
    description = "ecommerce"

    def __init__(self):
        self.applications = []
        self.services = systemservices.SystemServices(url.URL.fromString('/').child(ECommerceComponent.name).child('system'))

    def addApplication(self, application):
        application.setParent(self)
        self.applications.append(application)

    def initialize(self, realm):
        for application in self.applications:
            application.initialize(realm)

    def getComponents(self):
        return [ECommerceComponent(self)]

    def addService(self, name, service):
        service.setApplication(self)
        self.services.addService(name, service)

    def applicationByName(self, name):
        """
        Find the named application.
        """
        for application in self.applications:
            if application.name == name:
                return application
        raise KeyError("No application called %r"%name)


class ECommerceComponent(object):
    implements(itub.IApplicationPackage)

    name = 'ecommerce'
    label = 'ECommerce'
    description = 'ECommerce'

    def __init__(self, parent):
        self.parent = parent

    def getComponents(self):
        rv = []
        for application in self.parent.applications:
            rv = rv + application.getComponents()

        return rv

    def resourceFactory(self, avatar, storeSession, segments):

        if segments:
            for component in self.getComponents():
                if component.name == segments[0]:
                    return component.resourceFactory(avatar, storeSession, segments[1:])

        return web.ApplicationsPage(self), segments

    def getServices(self):
        return self.parent.services

    services = property(getServices)

class ECommerceAssets(systemservices.Assets):
    """Generic serve up a poop item"""

    assetBrowser = assetbrowser.AssetBrowser

    def getContentItem(self, avatar, storeSession, id, version):
        d = storeSession.getItemById(id)
        return d
    
    def locateChild( self, ctx, segments ):
        if segments[0] == self.assetBrowser.name:
            return self.assetBrowser(self.application), segments[1:]
        return systemservices.Assets.locateChild(self, ctx, segments)    


