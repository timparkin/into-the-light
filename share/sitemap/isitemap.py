from zope.interface import Interface

class ISiteMapSource(Interface):

    def getName(self):
        """Return the application name, used by site map to identify which ids came from
           which application"""
        pass

    def findItemsByIds(self, avatar, storeSession, ids):
        """Given an array of ids return the items"""
        pass

    def getNamesOfItems(self, avatar, storeSession):
        """Called by site map to get a list of items that can appear in the site map"""
        pass


class ISiteMapTitleProvider(Interface):

    def getTitle(self, ctx):
        """Called by site map to get the title for display"""
