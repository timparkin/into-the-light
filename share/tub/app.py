import itertools

from zope.interface import implements
from twisted.cred import checkers, credentials
from twisted.internet import defer
from twisted.python.components import registerAdapter
from twisted.python import log, reflect
from nevow import inevow
from crux import app, icrux, skin
from poop import objstore

from tub import category, itub, user, converterservice
from tub.acl import createPermissiveACL
from tub.apps.categories.app import CategoriesApplication
from tub.apps.users.app import UsersApplication

from tub.language import Language


defaultSkin = skin.PackageSkin('tub.web.templates')

class SystemServices(object):


    def __init__(self, config):
        if config is None:
            print '*** Please configure the systemServices in the config ***'
            config = []
        self.services = {}

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
    implements(itub.IRealm)

    languages = (Language('en', 'English', 'English'),)
    defaultLanguage = 'en'

    _cmsAssetsService = None


    def __init__(self, application, title, store, applications=None, acl=None, config=None):
        """
        Create a new Realm instance.

        * ``application`` - the Twisted service.Application instance
        * ``title`` - a nice title for the application to use
        * ``store`` - a storage instance, probably a tub.store.TubStore
        * ``applications`` - a sequence of itub.IApplication instances that will
                be hosted in the Tub's shell.  'Home', 'Categorisation', and
                'Users' applications will be automatically installed.
        """
        super(Realm, self).__init__(application)

        # Register the User type with the store before we do anything else.
        store.registerType(user.User)

        # Set myself up
        self.title = title
        self.store = store
        self._initApplications(applications)

        # Create a permissive ACL if not provided with an ACL configuration.
        if acl is None:
            acl = createPermissiveACL()
        self.acl = acl
        
        # Create the system services from the config
        self.config = config
        if config is not None and 'adminSystemServices' in config:
            self.systemServices = SystemServices(config.get('adminSystemServices'))
        else:
            self.systemServices = None
        

    def setLanguages(self, languages, default):
        """
        Set the languages for the application.

          * langauges: sequence of Language instances.
          * default: the code of the default language
        """
        if default not in [l.code for l in languages]:
            raise ValueError('Default language %r does not appear in list of '
                    'languages' % (default,))
                    
    def getFallbackLanguages(self):
        return (self.defaultLanguage,) + tuple(l.code for l in self.languages)
        
    fallbackLanguages = property(getFallbackLanguages)

    def _initApplications(self, applications):
        # Build the applications list
        self.applications = Applications(self)
        self.applications.addApplication(CategoriesApplication(), priority=99)
        self.applications.addApplication(UsersApplication(), priority=99)
        if applications is not None:
            for application in applications:
                self.applications.addApplication(application)

    def anonymousAvatarFactory(self):
        return AnonymousAvatar(self)

    def avatarFactory(self, avatarId):
        """
        Create an avatar to represent the authenticated user with the given id.
        """
        def gotUser(user):
            return Avatar(self, avatarId, user), lambda: None
        d = self.store.runInSession(lambda session:
                session.getItemById(avatarId))
        d.addCallback(gotUser)
        return d



class Applications(object):
    """
    Handles the installed applications of the realm.
    """

    def __init__(self, realm):
        self._realm = realm
        self._applications = []
        self._appcounter = itertools.count()

    def addApplication(self, application, priority=50):
        """
        Add an application to the list of installed applications.

        * ``application``: the application to add
        * ``priority``: the priority of the application. This will determine
                where the appliaction is display in the list.
        """
        self._applications.append( (priority, self._appcounter.next(),
            application) )
        self._applications.sort()
        application.initialize(self._realm)

    def iterApplications(self):
        """
        Iterate the installed applications in the correct order.
        """
        for appRecord in self._applications:
            yield appRecord[2]

    def iterComponents(self):
        """
        Iterate the components provided by the installed applications.
        """
        for app in self.iterApplications():
            for component in app.getComponents():
                yield component

    def applicationByName(self, name):
        """
        Find the named application.
        """
        for application in self.iterApplications():
            if application.name == name:
                return application
        raise KeyError("No application called %r"%name)

    __getitem__ = applicationByName

    def componentByName(self, name):
        """
        Find and return the application component with the given name. Raises a
        KeyError if the component cannot be found.
        """
        for component in self.iterComponents():
            if component.name == name:
                return component
        raise KeyError('No component called %r'%name)



class AvatarApplications(object):
    """
    Restricted-access wrapper to limit the applications and components of
    applications available to a user, based on the acl stored on the realm.
    """


    def __init__(self, avatar):
        self.avatar = avatar


    def iterApplications(self):
        for app in self.avatar.realm.applications.iterApplications():
            if self.avatar.hasAccess(app.name):
                yield AvatarApplication(self.avatar, app)


    def iterComponents(self):
        for app in self.iterApplications():
            for component in app.getComponents():
                yield app.application, component


    def applicationByName(self, name):
        for application in self.iterApplications():
            if application.name == name:
                return application
        raise KeyError("No application called %r"%name)

    __getitem__ = applicationByName


    def componentByName(self, name):
        for application, component in self.iterComponents():
            if component.name == name:
                return application, component
        raise KeyError('No component called %r'%name)



class AvatarApplication(object):
    """
    Restricted-access wrapper that checks a component is accessible according
    the acl.
    """


    def __init__(self, avatar, application):
        self.avatar = avatar
        self.application = application


    def getComponents(self):
        for comp in self.application.getComponents():
            permission = '%s.%s' % (self.application.name, comp.name)
            if self.avatar.hasAccess(permission):
                yield comp


    name = property(lambda self: self.application.name)
    version = property(lambda self: self.application.version)
    label = property(lambda self: self.application.label)
    description = property(lambda self: self.application.description)



class AnonymousAvatar(app.AnonymousAvatar):

    def __init__(self, *a, **k):
        super(AnonymousAvatar, self).__init__(*a, **k)
        self.id = None


class Avatar(object):
    implements(itub.IAvatar, icrux.IAvatar)

    def __init__(self, realm, avatarId, user):
        self.realm = realm
        self.id = avatarId
        self.user = user

    # Return an applications manager that checks acl-based access.
    applications = property(lambda self: AvatarApplications(self))

    def getUserManager(self, sess):
        return defer.succeed(user.UserManager(self, sess))

    def getCategoryManager(self, sess):
        return defer.succeed(category.CategoryManager(self, sess))

    def hasAccess(self, permission):
        return self.realm.acl.hasAccess(self.user.roles, permission)


class CredentialsChecker(object):
    """
    A twisted.cred credentials checker to authenticate users trying to access
    the site.
    """
    implements(checkers.ICredentialsChecker)

    credentialInterfaces = (credentials.IUsernamePassword,)

    def __init__(self, realm):
        self.realm = realm

    def requestAvatarId(self, creds):
        def findUser(session, username, password):
            return session.getItems(itemType=user.User,
                    where="username=%(username)s and password=%(password)s",
                    params={'username':username, 'password':password})
        def foundUser(users):
            try:
                user = users.next()
            except StopIteration:
                from twisted.cred.error import UnauthorizedLogin
                raise UnauthorizedLogin()
            return user.id
        d = self.realm.store.runInSession(findUser, creds.username,
                creds.password)
        d.addCallback(foundUser)
        return d


class OpenIDCredentialsChecker(object):
    """
    A twisted.cred credentials checker to authenticate users trying to access
    the site.
    """
    implements(checkers.ICredentialsChecker)

    credentialInterfaces = (icrux.IOpenIDCredentials,)

    def __init__(self, realm):
        self.realm = realm

    def requestAvatarId(self, creds):

        def findUser(session, openid):
            return session.getItems(itemType=user.User,
                    where="normalized_openid = %(openid)s",
                    params={'openid': openid})

        def foundUser(users):
            try:
                user = users.next()
            except StopIteration:
                from twisted.cred.error import UnauthorizedLogin
                raise UnauthorizedLogin()
            return user.id
        d = self.realm.store.runInSession(findUser, creds.openid)
        d.addCallback(foundUser)
        return d


def anonymousAvatarResourceFactory(avatar):
    """
    Lazily import the login module and create a LoginPage resource for
    unauthentication users.
    """
    from tub.web.login import LoginPage
    from tub.web.wrappers import TransactionalResourceWrapper, \
            SkinSetupResourceWrapper
    return SkinSetupResourceWrapper(
            TransactionalResourceWrapper(LoginPage(avatar), avatar),
            defaultSkin)


def avatarResourceFactory(avatar):
    """
    Lazily import the web module and create a RootPage resource to represent the
    authenticated user.
    """
    from tub.shell.web import RootPage
    from tub.web.wrappers import TransactionalResourceWrapper, \
            SkinSetupResourceWrapper
    return SkinSetupResourceWrapper(
            TransactionalResourceWrapper(RootPage(avatar), avatar),
            defaultSkin)


registerAdapter(anonymousAvatarResourceFactory, app.AnonymousAvatar, inevow.IResource)
registerAdapter(avatarResourceFactory, itub.IAvatar, inevow.IResource)
