import warnings
import mimetypes
from nevow import inevow, rend, appserver, url, loaders, static
from zope.interface import implements
from twisted.internet import defer
from twisted.python import log

import os, datetime

from pollen.nevow import imaging

from tub import itub
from tub.web import util
from cms import icms, web, assetbrowser

class SystemServices(rend.Page):
    implements(inevow.IResource)

    def __init__(self, u):
        self._url = u
        self._services = {}

    def addService(self, name, service):
        self._services[name] = service
        setattr(self, 'child_%s'%name, service)
        if hasattr(service, 'setURL'):
            service.setURL(self._url.child(name))

    def getService(self, name):
        return self._services[name]

#
#    def getSearchUrl(self, ctx):
#        currLanguage = inevow.ILanguages(ctx)[0]
#        defaultLanguage = portal.IRealm(ctx).defaultLanguage
#        u = url.URL.fromString('/')
#        if currLanguage != defaultLanguage:
#            u = u.child(currLanguage)
#        u = u.child('system').child(self._urls['search'])
#        return u



class Assets(object):
    implements( inevow.IResource )

    def __init__( self, cachedir ):
        self.cachedir = cachedir
        self.url = None
        self.application = None

    def setURL(self, url):
        self.url = url
    
    def setApplication(self, application):
        self.application = application

    def locateChild( self, ctx, segments ):

        def notFound( failure ):
            log.err(failure)
            return appserver.NotFound

        # Get hold of the store session and avatar from the context
        storeSession = util.getStoreSession(ctx)
        avatar = util.getAvatar(ctx)

        # First segment may be a language. It should be ok making this
        # assumption because the next segment is the id/version which can't look
        # like a country code.
        languageCodes = [l.code for l in avatar.realm.languages]
        if segments[0] not in languageCodes:
            # Try the current language buf it that's not a configured language
            # then just use the default.
            try:
                lang = inevow.ILanguages(ctx)[0]
            except IndexError:
                lang = None
            if lang not in languageCodes:
                lang = avatar.realm.defaultLanguage
        else:
            lang = segments[0]
            segments = segments[1:]

        # (Remaining) segments can be either (itemId,) or (itemId, assetName).
        if len(segments) == 1:
            itemId, assetName = segments[0], None
        elif len(segments) == 2:
            itemId, assetName = segments
        else:
            return appserver.NotFound

        d = self._getResource( avatar, storeSession, itemId, assetName, lang )
        d.addCallback(lambda resource: (resource, ()))
        d.addErrback( notFound )
        return d

    def getURLForImage( self, item, includeVersion=True, language=None ):
        warnings.warn("getURLForImage is deprecated use getURLForAsset in its place",
            DeprecationWarning, stacklevel=2)
        return self.getURLForAsset(item, includeVersion, language)

    def getURLForAsset( self, item, includeVersion=True, language=None ):
        rv = self.url
        if language is not None:
            rv = rv.child(language)
        rv = rv.child(web.encodeIdVersion(item.id,item.version, includeVersion))
        return rv

    def getPathForAsset(self, avatar, storeSession, asset, name, lang=None):

        d = self._getResourceAndPath(asset, avatar, storeSession, name, lang)
        d.addCallback(lambda res: res[1])
        return d

    def _isAssetCached(self, contentItem, assetName, lang):
        # Ideally I would like to get the mime type from DataProvider but that would
        # mean changing quite a lot, so I make an assumption.
        #
        # I look at files in the cache directory and if there is a match (without the extension)
        # then I check the mtime, if the file was written after the mtime on
        # the content item then I assume the file is current and use that file.

        import os.path

        filename = web.encodeIdVersion(contentItem.id,contentItem.version)
        filename = '_'.join(filter(None, [filename, assetName, lang]))

        dirList = os.listdir(self.cachedir)

        for file in dirList:
            root, ext = os.path.splitext(file)
            if root == filename:
                path = os.path.join(self.cachedir, file)
                filemtime = datetime.datetime.utcfromtimestamp( os.path.getmtime( path ) )
                if filemtime > contentItem.mtime:
                    mimetype = mimetypes.guess_type( file )[0]
                    
                    if mimetype.startswith('image'):
                        return imaging.ImageResource( path ), path
                    else:
                        return static.File(path), path

        return None, None


    def _getCachePath(self, contentItem, assetName, lang, mimetype, data):
        filename = web.encodeIdVersion(contentItem.id,contentItem.version)
        filename = '_'.join(filter(None, [filename, assetName, lang]))
        ext = mimetypes.guess_extension(mimetype)
        if ext is not None:
            filename = filename + ext
        path = os.path.join(self.cachedir, filename)

        # work out if the existing file, if any, is current
        writeFile = True
        if os.path.exists( path ):
            filemtime = datetime.datetime.utcfromtimestamp( os.path.getmtime( path ) )
            if filemtime > contentItem.mtime:
                writeFile = False

        if writeFile:
            image = open( path, "w" )
            image.write(data)
            image.close()

        return path

    def _getResource(self, avatar, storeSession, itemId, assetName, lang ):

        # The itemId may actually have the version encoded in it too
        id, version = web.decodeIdVersion(itemId)

        # Need to do this to check capabilities
        d = self.getContentItem(avatar, storeSession, id, version )
        d.addCallback(self._getResourceAndPath, avatar, storeSession, assetName, lang)
        d.addCallback(lambda res: res[0])
        return d

    def _getResourceAndPath(self, contentItem, avatar, storeSession, assetName, lang):

        asset, path = self._isAssetCached(contentItem, assetName, lang)
        if asset:
            return defer.succeed((asset, path))

        def gotData(assetData, contentItem):
            mimetype, data = assetData
            path = self._getCachePath(contentItem, assetName, lang, mimetype, data)
            if mimetype.startswith('image'):
                return imaging.ImageResource( path ), path
            else:
                return static.File(path), path

        def handleKeyError(failure):
            failure.trap(KeyError)
            return None, None

        # If we didn't find the content item then there's nothing more to do.
        if contentItem is None:
            return None

        dataProvider = None
        # Try to adapt to find the asset data.
        adapter = icms.IAssetDataProvider(contentItem, None)
        if adapter:
            dataProvider = adapter.provideData

        if not dataProvider:
            adapter = icms.IImageDataProvider(contentItem, None)
            if adapter is None:
                return None
            warnings.warn("icms.IImageDataProvider is deprecated use IAssetDataProvider in its place",
                DeprecationWarning, stacklevel=2)
            dataProvider = adapter.provideImageData

        d = defer.maybeDeferred( dataProvider, avatar, storeSession, assetName, [lang] )
        d.addCallback(gotData, contentItem)
        d.addErrback(handleKeyError)
        return d

    def getContentItem(self, avatar, sess, id, version):
        return self.application.getContentManager(avatar).publicFindById(sess, id)

class Images(Assets):
    def __init__(self, cachedir):
        super(Images, self).__init__(cachedir)
        warnings.warn('systemservices.Images is deprecated use systemservices.Assets in its place', 
            DeprecationWarning, stacklevel=2)


class AdminAssets(Assets):

    assetBrowser = assetbrowser.AssetBrowser

    def getContentItem(self, avatar, sess, id, version):
        return self.application.getContentManager(avatar).findById(sess, id, version)

    def locateChild( self, ctx, segments ):
        if segments[0] == self.assetBrowser.name:
            return self.assetBrowser(self.application), segments[1:]
        return Assets.locateChild(self, ctx, segments)

class AdminImages(AdminAssets):

    def __init__(self, *a, **kw):
        super(AdminImages, self).__init__(*a,**kw)
        warnings.warn("systemservices.AdminImages is deprecated use systemservices.AdminAssets in its place",
            DeprecationWarning, stacklevel=2)
            
