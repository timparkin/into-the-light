from zope.interface import implements
from twisted.internet import defer
from nevow import url

from tub import itub
from cms import systemservices

from basiccms.apps.artwork import web, manager


class ArtworkApplication(object):
    implements(itub.IApplication)

    name = "artwork"
    version = 1
    label = "Artwork Management"
    description = "Artwork Management"

    def __init__(self, assetService, indexer=None):
        self.indexer = indexer
        self._services = systemservices.SystemServices(url.URL.fromString('/').child(self.name).child('system'))
        self.addService('assets', assetService)

    def setParent(self, parent):
        self.parent = parent

    def initialize(self, realm):
        realm.store.registerType(manager.Artwork)

    def getComponents(self):
        return [ArtworkComponent(self)]

    def getManager(self):
        return defer.succeed(manager.ArtworkManager(self.indexer))

    def getServices(self):
        return self._services

    def addService(self, name, service):
        service.setApplication(self)
        self.services.addService(name, service)

    services = property(getServices)


class ArtworkComponent(object):
    implements(itub.IApplicationComponent)

    name = "artwork"
    label = "Artwork Management"
    description = "Artwork Management"

    def __init__(self, application):
        super(ArtworkComponent, self).__init__()
        self.application = application

    def resourceFactory(self, avatar, storeSession, segments):
        return web.ArtworkPage(self.application), segments

