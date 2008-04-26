from zope.interface import implements
from twisted.internet import defer

from tub import itub
from sitemap import web, manager, isitemap


class SiteMapApplication(object):
    implements(itub.IApplication)

    name = "sitemap"
    version = 1
    label = "Site Map Management"
    description = "Site Map management"


    def __init__(self):
        self.sources = {}
        self.reservedNodes = []
        self.navigationLevels = [
            (1, 'Primary'),
            ]

    def initialize(self, realm):
        pass

    def getComponents(self):
        return [SiteMapComponent(self)]

    def addContentSource(self, src):
        src = isitemap.ISiteMapSource(src)
        if self.sources.get(src.getName(), None):
            raise "SiteMap source with name %s already added"%src.getName()
        self.sources[src.getName()] = src

    def addReservedNodes(self, nodes):
        self.reservedNodes += nodes

    def setNavigationLevels(self, levels):
        self.navigationLevels = levels

    def getManager(self, avatar, storeSession):
        return manager.SiteMapManager(avatar, storeSession, self.sources, self.reservedNodes, self.navigationLevels)


class SiteMapComponent(object):
    implements(itub.IApplicationComponent)

    name = "sitemap"
    label = "Site Map"
    description = "Manage site map"

    def __init__(self, application):
        super(SiteMapComponent, self).__init__()
        self.application = application

    def resourceFactory(self, avatar, storeSession, segments):
        def gotSiteMap(siteMap, manager, segments):
            return web.SiteMapPage(siteMap, manager=manager), segments

        manager = self.application.getManager(avatar, storeSession)
        d = manager.loadSiteMap()
        d.addCallback(gotSiteMap, manager, segments)
        return d

def debug(r, msg):
    print '>>DEBUG', msg, r
    return r

