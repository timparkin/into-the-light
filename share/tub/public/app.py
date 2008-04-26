from zope.interface import implements
from twisted.python import log
from twisted.python import components, reflect
from nevow import inevow
from tub.language import Language
from crux import app

from tub.public import cmsservice, mailservice

# XXX This shouldn't be here
from crux import icrux
class CMSSystemAssetsResource(object):
    implements(inevow.IResource)

    def locateChild(self, ctx, segments):
        avatar = icrux.IAvatar(ctx)
        return avatar.realm.cmsAssetsService, segments

    def renderHTTP(self, ctx):
        avatar = icrux.IAvatar(ctx)
        return avatar.realm.cmsAssetsService


class SystemServices(object):


    def __init__(self, config):
        if config is None:
            print '*** Please configure the systemServices in the config ***'
            config = []
        self.services = {}

        # Add the CMS assets service if not explicitly configured (backwards
        # compat).
        if 'assets' not in [c['name'] for c in config]:
            self.addService('assets', CMSSystemAssetsResource())

        # Add the configured services
        for serviceConfig in config:
            log.msg('Installing %r system service' % serviceConfig['name'])
            factory = reflect.namedAny(serviceConfig['factory'])
            service = factory(**serviceConfig['args'])
            self.addService(serviceConfig['name'], service)


    def addService(self, name, service):
        self.services[name] = service


    def getService(self, name):
        return self.services[name]


class Realm(app.Realm):
    """
    Realm for the public application.
    """

    languages = (Language('en', 'English', 'English'),)
    defaultLanguage = 'en'

    _mailService = None
    _cmsService = None
    _cmsAssetsService = None
    _siteMapService = None

    def __init__(self, application, config, store, siteId, urlMappings=None):
        super(Realm, self).__init__(application)
        # Save reference to config
        self.config = config
        # Save a reference to the store and register the CMS types we use.
        self.store = store
        cmstypes = []
        for cmstypeAndArgs in self.config.get('cmstypes',[]):
            pluginClass = reflect.namedAny(cmstypeAndArgs[0])
            pc=pluginClass(*cmstypeAndArgs[1:])
            cmstypes.append(pc.contentItemClass)
            self.store.registerType(*cmstypes)

        self.siteId = siteId
        self.systemServices = SystemServices(config.get('systemServices'))

        self.urlMappings = urlMappings

    
    def getFallbackLanguages(self):
        return (self.defaultLanguage,) + tuple(l.code for l in self.languages)
        
    fallbackLanguages = property(getFallbackLanguages)

    
    def getCMSService(self):
        if self._cmsService is None:
            self._cmsService = cmsservice.CMSService()
        return self._cmsService

    cmsService = property(getCMSService)

    def getCMSAssetsService(self):
        if self._cmsAssetsService is None:
            self._cmsAssetsService = cmsservice.AssetsService(self.config['cmsAssetsService']['cachedir'])
        return self._cmsAssetsService

    cmsAssetsService = property(getCMSAssetsService)

    def getMailService(self):
        if self._mailService is None:
            self._mailService = mailservice.MailService(self.siteId, self.config)
        return self._mailService

    mailService = property(getMailService)

    def getSiteMapService(self):
        from tub.public import sitemapservice

        if self._siteMapService is None:
            self._siteMapService = sitemapservice.SiteMapService(self.config['sitemapsources'])
        return self._siteMapService

    siteMapService = property(getSiteMapService)

    def anonymousAvatarFactory(self):
        return AnonymousAvatar(self), lambda: None


class AnonymousAvatar(app.AnonymousAvatar):
    id = None
        
