"""
Code common to all the other web code.
"""

import datetime
from zope.interface import implements
from twisted.internet import defer
from twisted.python import log
from poop import store
from nevow import flat, inevow, tags as T, url
from crux import icrux, skin, web

from tub.public.web import wrappers


class PageMixin(object):
    """
    PageMixin provides a docFactory loader that skins the site, leaving a "hole"
    that is filled with whatever the content attribute provides.
    """
    
    docFactory = skin.loader('Skin.html')
    content = None

    def locateChild(self, ctx, segments):
        ctx.remember(self, inevow.ICanHandleNotFound)
        return super(PageMixin, self).locateChild(ctx, segments)
        
    def renderHTTP_notFound(self, ctx):
        avatar = icrux.IAvatar(ctx)
        storeSession = getStoreSession(ctx)
        if storeSession:
            storeSession.forceRollback = True
        return wrappers.TransactionalResourceWrapper(NotFoundPage(), avatar)
        
    def macro_content(self, ctx):
        if self.content is None:
            raise Exception('No content for %r'%self.__class__.__name__)
        def render(ctx, data):
            return self.content
        return render
        
    def render_title_tag(self, ctx, data):
        return ctx.tag

    def render_meta_keywords(self, ctx, data):
        return ctx.tag

    def render_meta_description(self, ctx, data):
        return ctx.tag

    def render_simpleBreadcrumb(self, ctx, data):
        # Get a url and a path list
        u = url.URL.fromContext(ctx)
        pathList = u.pathList(copy=True)
        if not pathList[0]:
            pathList = pathList[1:]
        pathList = ['home'] + pathList

        # Work from right to left
        pathList.reverse()

        rv = []
        first = True
        while pathList:
            tag = T.a(href=u)[pathList[0]]
            if first:
                # Right most element is not a link
                first = False
                tag = pathList[0]
            rv.append(tag)

            # set up for next iteration
            u = u.up()
            pathList = pathList[1:]
            if pathList:
                rv.append(' > ')
        
        # Switch so it reads left to right
        rv.reverse()

        return ctx.tag[rv]


class Page(PageMixin, web.Page):
    """
    Base page for all other pages in the application.
    """
    def __init__(self, *a, **k):
        super(Page, self).__init__(*a, **k)


class StoreSessionClosingResource(object):
    implements(inevow.IResource)
    
    def __init__(self, resource):
        self.resource = resource
        
    def locateChild(self, ctx, segments):
        return self.resource.locateChild(ctx, segments)
        
    def renderHTTP(self, ctx):
        d = closeStoreSession(ctx)
        d.addCallback(lambda ignore: self.resource.renderHTTP(ctx))
        return d

            
class Fragment(web.Fragment):
    pass

        
class NotFoundPage(Page):
    """
    Not found page.
    """
    content = skin.loader('NotFound.html', ignoreDocType=True)


def getStoreSession(ctx):
    """
    Get and return a store session for the current request. A new store session
    will be created if one has not been created already.
    """
    request = inevow.IRequest(ctx)
    return request.getComponent(store.IStoreSession)
    

def closeStoreSession(ctx):
    request = inevow.IRequest(ctx)
    storeSession = request.getComponent(store.IStoreSession)
    if storeSession is not None:
        request.unsetComponent(store.IStoreSession)
        return storeSession.close()
    return defer.succeed(None)
    

DATE_FORMAT = '%d/%m/%Y'
TIME_FORMAT = '%H:%M'
DATETIME_FORMAT = DATE_FORMAT + ', ' + TIME_FORMAT

    
def dateFlattener(date, ctx):
    return date.strftime(DATE_FORMAT)
    

def timeFlattener(time, ctx):
    return time.strftime(TIME_FORMAT)


def datetimeFlattener(datetime, ctx):
    return datetime.strftime(DATETIME_FORMAT)


flat.registerFlattener(dateFlattener, datetime.date)
flat.registerFlattener(timeFlattener, datetime.time)
flat.registerFlattener(datetimeFlattener, datetime.datetime)


def RichTextFlattener(original, ctx):
    from cms.widgets.restsupport import publicCmsReSTWriter
    return T.xml(original.htmlFragment(restWriter=publicCmsReSTWriter))


from cms.widgets import richtext
if flat.getFlattener( richtext.RichTextData(None) ) is None:
    flat.registerFlattener(RichTextFlattener, richtext.RichTextData)



class CMSMixin(object):
    """
    Convenience class for CMS-based pages.
    """

    def render_title_tag(self, ctx, data):
        tag = ctx.tag

        if not self.original:
            return tag

        avatar = icrux.IAvatar(ctx)
        value = self.original.getSystemAttributeValue('titleTag', avatar.realm.defaultLanguage)
        if value:
            tag = ctx.tag.clear()
            tag = tag[value]
        return tag


    def render_meta_keywords(self, ctx, data):
        tag = ctx.tag

        if not self.original:
            return tag

        avatar = icrux.IAvatar(ctx)
        value = self.original.getSystemAttributeValue('metaKeywords', avatar.realm.defaultLanguage)
        if value:
            tag = tag(content=value)
        return tag


    def render_meta_description(self, ctx, data):
        tag = ctx.tag

        if not self.original:
            return tag

        avatar = icrux.IAvatar(ctx)
        value = self.original.getSystemAttributeValue('metaDescription', avatar.realm.defaultLanguage)
        if value:
            tag = tag(content=value)
        return tag


    def data_itemattr(self, name):
        """
        Retrieve and item attribute by name.
        """
        def data_itemattr(ctx, data):
            avatar = icrux.IAvatar(ctx)
            try:
                return self.original.getAttributeValue(name, avatar.realm.defaultLanguage)
            except Exception, e:
                # This is on the public site, the caller was expecting something
                # to be returned so I'll give them an empty string but log the
                # error
                log.err('ERROR: data_itemattr trying to get value for attribute %s'%name)
                log.err(e)
                return ''
        return data_itemattr



class CMSPage(Page, CMSMixin):
    pass
