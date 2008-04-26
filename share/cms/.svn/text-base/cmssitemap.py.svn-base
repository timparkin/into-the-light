from zope.interface import implements
from twisted.python import components
from sitemap import isitemap 

from cms import app

class CMSSiteMapSource(object):
    implements(isitemap.ISiteMapSource)

    def __init__(self, application):
        self.application = application

    def getName(self):
        # This has to match the public site and any 
        # RI triggers
        return 'cms'

    def findItemsByIds(self, avatar, storeSession, ids):
        raise NotImplementedError()

    def getNamesOfItems(self, avatar, storeSession):
        cm = self.application.getContentManager(avatar)
        return cm.getNamesOfItems(storeSession)

components.registerAdapter(CMSSiteMapSource, app.ContentApplication, isitemap.ISiteMapSource)
