from zope.interface import implements
from tub import itub

from cms import contentindex, contentitem, web, systemservices
from nevow import url



class FragmentComponent(object):
    """
    A "Content" component for a particular content type.
    """
    implements(itub.IApplicationComponent)

    def __init__(self, application):
        self.application = application

    name = 'fragment'

    label = 'Fragments'

    description = 'Fragment Manager'

    def resourceFactory(self, avatar, storeSession, segments):
        if len(segments) > 0 and segments[0] == 'types':
            return web.FragmentsTypesPage(avatar, self.application), segments[1:]
        return web.FragmentsPage(avatar, self.application), segments    
    

class ContentApplication(object):
    """

    """
    implements(itub.IApplication)

    name = 'content'
    version = '0.1'
    label = 'Content Management'
    description = 'Manage content items.'

    contentIndex = None

    def __init__(self, sitemapManagerFactory=None, listFacets=None):
        self.contentTypes = ContentTypes()
        self.services = systemservices.SystemServices(url.URL.fromString('/').child(ContentComponent.name).child('system'))
        self.listFacets = listFacets
        self.sitemapManagerFactory = sitemapManagerFactory
        if not self.listFacets:
            self.listFacets = []
        self.__realm = None

    def isManagingSitemap(self):
        return self.sitemapManagerFactory is not None

    def initialize(self, realm):
        self.__realm = realm
        for contentType in self.contentTypes:
            contentType.initialize(realm)
        self.contentIndex = contentindex.NullContentIndex()

    def addContentType(self, contentType):
        """
        Add a content type that this application should support.
        """
        contentType.setApplication(self)
        self.contentTypes.addContentType(contentType)
        if self.__realm is not None:
            contentType.initialize(self.__realm)

    def getComponents(self):
        """
        Return a list conaining the main component of the application. That
        component will have a number of subcomponents for the content types.
        """
        if self.isManagingSitemap():
            return [ContentComponent(self, noPages=True), PagesComponent(self), FragmentComponent(self)]
        else:
            return [ContentComponent(self)]

    def getContentManager(self, avatar):
        return contentitem.ContentManager(avatar, self)

    def addService(self, name, service):
        service.setApplication(self)
        self.services.addService(name, service)

class ContentComponent(object):
    """
    The main "Content" component.

    This is really just a placeholder for the content type components but it
    could be an aggregate component of some sort in the future.
    """
    implements(itub.IApplicationPackage)

    name = 'content'
    label = 'Content'
    description = 'Content'

    def __init__(self, application, noPages=False):
        self.application = application
        self.noPages = noPages

    def getComponents(self):
        """
        Return a list of components, one for each content type.
        """
        contentTypes = self.application.contentTypes
        if self.noPages:
            contentTypes = (ct for ct in contentTypes if 'Page' not in ct.name and 'Fragment' not in ct.name)
        return [ContentTypeComponent(self, ct) for ct in contentTypes]

    def resourceFactory(self, avatar, storeSession, segments):
        if segments:
            type = self.application.contentTypes.get(segments[0])
        if not segments or type is None:
            return web.ContentItemsPage(avatar, self.application, None), segments

        return ContentTypeComponent(self.application,
                type).resourceFactory(avatar, storeSession, segments[1:])


class PagesComponent(object):
    """
    The main "Content" component.

    This is really just a placeholder for the content type components but it
    could be an aggregate component of some sort in the future.
    """

    implements(itub.IApplicationComponent)

    def __init__(self, application):
        self.application = application

    name = 'Pages'

    label = name

    description = property(lambda self: self.contentType.description)

    def resourceFactory(self, avatar, storeSession, segments):
        return web.SitemappedItemsPage(avatar, self.application), segments    
    



class ContentTypeComponent(object):
    """
    A "Content" component for a particular content type.
    """
    implements(itub.IApplicationComponent)

    def __init__(self, application, contentType):
        self.application = application
        self.contentType = contentType

    name = property(lambda self: self.contentType.name)

    label = name

    description = property(lambda self: self.contentType.description)

    def resourceFactory(self, avatar, storeSession, segments):
        return web.ContentItemsPage(avatar, self.application, self.contentType), segments




class ContentTypes(object):
    """
    Content type registry for tracking all content types installed for a
    ContentApplication.
    """
    
    def __init__(self):
        self.types = []

    def addContentType(self, contentType):
        self.types.append(contentType)

    def get(self, contentTypeName, default=None):
        for type in self:
            if type.name == contentTypeName:
                return type
        return default

    def getTypeForItem(self, item):
        for type in self:
            if type.contentItemClass.__typename__ == item.__typename__:
                return type
        raise KeyError(item.__typename__)

    def __getitem__(self, contentTypeName):
        type = self.get(contentTypeName)
        if type is not None:
            return type
        raise KeyError("No content type with name %r" % contentTypeName)

    def __iter__(self):
        return iter(self.types)
