"""
Todo:
   * Exception
"""

from zope.interface import implements
from twisted.internet import defer
from nevow import appserver, inevow, rend, url
from tub.public.web import common as tubcommon, pages, wrappers
from crux import icrux, skin, web

# Import module to register IResource adapters
from basiccms.web import cmsresources, gallery, blog, basket, search



class RootResource(rend.Page):
    """
    Basic root controller resource.

    The root controller resource provides:
       * Access to public skin resource
       * Access to system services resource
       * Lookup of CMS items (using sitemap)
       * Standard 404 handler
    """

    implements(inevow.IResource)


    def __init__(self, avatar):
        rend.Page.__init__(self)
        self.avatar = avatar
        self.remember(self.avatar, icrux.IAvatar)

    def locateChild(self, ctx, segments):

        #ctx.remember(self, inevow.ICanHandleNotFound)
        #ctx.remember(self, inevow.ICanHandleException)

        def childLocated(result):
            # :sigh: it might be deferred
            if isinstance(result[0], defer.Deferred):
                result[0].addCallback(lambda r: (r, result[1]))
                result[0].addCallback(childLocated)
                return result[0]
            # Return a sane resource
            if result is not appserver.NotFound and result[0] is not None:
                return result
            # Or look for a CMS managed item.
            return self.locateCMSResource(ctx, segments)

        # Try to resolve application-fixed resources.
        d = defer.maybeDeferred(super(RootResource, self).locateChild, ctx,
                segments)
        d.addCallback(childLocated)
        return d


    def child_skin(self, ctx):
        return skin.SkinResource()


    def child_system(self, ctx):
        return pages.SystemServicesResource(self.avatar.realm.systemServices)

    def child_content(self, ctx):
        return pages.SystemServicesResource(self.avatar.realm.systemServices)


    def child_gallery(self,ctx):
        return gallery.Gallerys()

    def child_gallerysearch(self, ctx):
        return search.SearchPage(self.avatar,
            url.URL.fromString('/product'),url.URL.fromString('/basket'))

    def child_search(self, ctx):
        return search.StaticSearchPage(self.avatar,'clearfix')

    def child_blog(self,ctx):
        return blog.Blog()

    def child_basket(self, ctx):
        return basket.BasketPage(self.avatar, url.URL.fromString('/basket'))
    
    def child_rss(self, ctx):
        return blog.BlogRSS(ctx)
    
    
    def locateCMSResource(self, ctx, segments):
        """
        Locate and return the best match from the site map.
        """
        return pages.siteMapBestMatch(ctx, segments)


    def notFoundFactory(self, ctx, avatar):
        return NotFoundPage()




class NotFoundPage(web.Page):

    docFactory = skin.loader("NotFound.html")



def notFoundResourceFactory(ctx):
    storeSession = tubcommon.getStoreSession(ctx)
    if storeSession:
        storeSession.forceRollback = True
    return NotFoundPage()
