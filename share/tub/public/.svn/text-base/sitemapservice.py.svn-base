# This module will allows the public tub application site to access content from
# the site map application.

from zope.interface import implements, Interface
from twisted.python.reflect import namedAny
from twisted.python import components
from sitemap import manager, isitemap
from nevow import inevow, context

from crux import icrux
from tub.public.web import common

from cms import contentitem

class ISiteMapMarker(Interface):
    """Marker interface for the site map manager"""


class PublicCMSSiteMapSource(object):
    implements(isitemap.ISiteMapSource)

    def getName(self):
        return 'cms'

    def findItemsByIds(self, avatar, storeSession, ids):
        return avatar.realm.cmsService.getItemsByIds(storeSession, avatar, ids)

    def getNamesOfItems(self, avatar, storeSession):
        raise NotImplementedError()


class CMSItemSiteMapTitleProvider(object):
    implements(isitemap.ISiteMapTitleProvider)

    def __init__(self, item):
        self.item = item

    def getTitle(self, ctx):
        avatar = icrux.IAvatar(ctx)
        return self.item.getAttributeValue('title', avatar.realm.defaultLanguage)

components.registerAdapter(CMSItemSiteMapTitleProvider, contentitem.ContentItem, isitemap.ISiteMapTitleProvider)

class SiteMapService(object):

    def __init__(self, siteMapSources):
        self.sources = {}
        for srcName in siteMapSources:
            src = namedAny(srcName)()
            self.sources[src.getName()] = src

    def _findRequestCtx(self, ctx):
        while ctx:
            if isinstance(ctx, context.RequestContext):
                return ctx
            ctx = ctx.parent
        return None        

    def getManager(self, ctx):
        try:
            return ctx.locate(ISiteMapMarker)
        except KeyError:
            avatar = icrux.IAvatar(ctx)
            storeSession = common.getStoreSession(ctx)

            mgr = manager.SiteMapManager(avatar, storeSession, self.sources )
            rCtx = self._findRequestCtx(ctx)
            if rCtx:
                rCtx.remember( mgr, ISiteMapMarker)
            return mgr
