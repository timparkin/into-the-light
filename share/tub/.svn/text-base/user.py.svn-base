from zope.interface import implements
from twisted.cred import checkers, credentials, error
from twisted.internet import defer
from poop import objstore
from tub.error import TubError
from tub.capabilities import GroupPermission, CommonPermissions, requiredPermissions, permissionRegistry


# System-wide capability resource aliases
CAPABILITY_USER_MGR_ALIAS = 'tub/users'
CAPABILITY_ADMIN_USER_ALIAS = 'tub/users/admin'


# Permissions
READ_USER = CommonPermissions.READ
UPDATE_USER = CommonPermissions.UPDATE
UPDATE_CAPABILITIES = CommonPermissions.UPDATE_CAPABILITIES
DELETE_USER = CommonPermissions.DELETE
UPDATE_SUSPENDED = CommonPermissions.UPDATE_SUSPENDED


class UserExistsError(TubError):
    """
    Exception raised when a new user being added to the system includes
    attributes that make the user non-unique.
    """
    pass


def normalizeUrl(url):
    if not url:
        return url

    try:
        import crux.openidconsumer
        return crux.openidconsumer.normalizeUrl(url)
    except:
        return url


class User(objstore.Item):
    """I represent a user in the system.
    
    A user is used to provide authentication and provides an ID to hang
    permissions off that control the level of access a user has.
    """

    __table__ = 'usr'
    username = objstore.column()
    password = objstore.column()
    normalizedOpenid = objstore.column('normalized_openid')

    def __init__(self, session, id, username, password, email=None,
            firstName=None, lastName=None, roles=None, openid=None):
        super(User, self).__init__(session, id)
        self.username = username
        self.password = password
        self.email = email
        self.firstName = firstName
        self.lastName = lastName
        self.suspended = False
        if roles is None:
            roles = []
        self.roles = roles
        # The open id the user enters
        self.openid = openid
        # The open id the system uses
        self.normalizedOpenid = normalizeUrl(openid)

    def __getattr__(self, name):
        """
        Intercept 'roles' attribute access so that existing User instances
        magically get the roles attribute.
        """
        if name == 'roles':
            self.roles = []
            return self.roles
        return super(User, self).__getattr__(name)
    
    def _makeName(self):
        """Convenience method to create a full name in a consistent format.
        Don't actually call this method though; use the name property.
        """
        names = [name for name in (self.firstName, self.lastName) if name]
        if names:
            return ' '.join(names)
        return self.username
        
    name = property(_makeName)

    @requiredPermissions(UPDATE_USER)
    def update(self, data):
        for name, value in data.iteritems():
            # Don't update password if not changed
            if name == 'password' and value is None:
                continue
            if name == 'suspended':
                continue
            setattr(self, name, value)
            if name == 'openid':
                self.normalizedOpenid = normalizeUrl(value)
        self.touch()

    @requiredPermissions(READ_USER)
    def find(self):
        return self

    @requiredPermissions(DELETE_USER)
    def delete(self, sess):
        return sess.removeItem(self.id)

    @requiredPermissions(UPDATE_CAPABILITIES)
    def updateCapabilities(self, sess, objects, toAdd, toRemove):
        d = self._accessorsForObjects(objects, sess)
        d.addCallback(self._updateCapabilities, sess, toAdd, toRemove)
        return d

    @requiredPermissions(UPDATE_SUSPENDED)
    def setSuspended(self, newValue):
        self.suspended = newValue
        self.touch()

    def getPermissionsForObjects(self, ctx, permissions, objects):
        def munge(objectsAndAccessors):
            rv = []
            for o, accessor in objectsAndAccessors:
                permDict = {'type': o.description, 'name': o.name, 'permissions': {}}
                for permission in permissions:
                    permDict['permissions'][permission.name] = accessor.testCapability(permission)
                rv.append(permDict)
            return rv
        # XXX mg: Deliberate breakage. I really don't think a Nevow context
        # should get in here so I removed the icms import from the top of the
        # module :).
        sess = icms.IStoreSession(ctx)
        d = self._accessorsForObjects(objects, sess)
        d.addCallback(munge)
        return d

    @defer.deferredGenerator
    def _accessorsForObjects(self, objects, sess):
        """Turn a sequence of objects into a sequence of (object, accessor)
        tuples for the user being edited.
        """
        rv = []
        for o in objects:
            d = defer.waitForDeferred(sess.capCtx.getCapabilityAccessor(o, self.id))
            yield d
            accessor = d.getResult()
            rv.append((o,accessor))
        yield rv

    @defer.deferredGenerator
    def _updateCapabilities(self, objectsAndAccessors, sess, toAdd, toRemove):
        oaMap = dict((o.name,(o,a)) for o,a in objectsAndAccessors)
        for objectName, permissionName in toAdd:
            o, accessor = oaMap[objectName]
            permission = permissionRegistry[permissionName]
            d = defer.waitForDeferred(accessor.addCapability(permission))
            yield d
            d.getResult()
        for objectName, permissionName in toRemove:
            o, accessor = oaMap[objectName]
            permission = permissionRegistry[permissionName]
            d = defer.waitForDeferred(accessor.removeCapability(permission))
            yield d
            d.getResult()

    
CREATE_USER = GroupPermission(CommonPermissions.CREATE,
        CAPABILITY_USER_MGR_ALIAS)


class UserManager(object):
    """The user manager is responsible for creating, finding and removing users.
    All user access should go through a UserManager instance.
    
    Typically, there will be a user manager attached to the avatar so go look
    there first.
    """
    alias = CAPABILITY_USER_MGR_ALIAS
    description = 'User Manager'
    name = 'usermanager'

    PERMISSIONS_FOR_CREATING_USER = (READ_USER, UPDATE_USER, DELETE_USER, UPDATE_CAPABILITIES, UPDATE_SUSPENDED)
    
    def __init__(self, avatar, sess):
        """Initialise the user manager.
        
        avatar:
            The current user's avatar.
        sess:
            A store session.
        """
        self.avatar = avatar
        self.sess = sess
    
    @requiredPermissions(CREATE_USER)
    def createUser(self, *a, **k):
        """Create a new user. Any args passed to this method are passed on to
        the User factory.
        """

        def createUser(ignore):
            d = self.sess.createItem(User, *a, **k)
            return d

        def addCapabilities(obj):
            def addCapability(accessor, permission):
                d = accessor.addCapability(permission)
                d.addCallback(lambda ignore: accessor)
                return d
            
            # add capabilities to the creating user
            d = self.sess.capCtx.getCapabilityAccessor(obj)
            for permission in UserManager.PERMISSIONS_FOR_CREATING_USER:
                d.addCallback(addCapability, permission)
            # add capabilities to the admin user
            d.addCallback(lambda ignore:
                    self.sess.capCtx.getCapabilityAccessor(obj,
                        CAPABILITY_ADMIN_USER_ALIAS))
            for permission in UserManager.PERMISSIONS_FOR_CREATING_USER:
                d.addCallback(addCapability, permission)
            # add capabilities to the new user
            d.addCallback(lambda ignore: self.sess.capCtx.getCapabilityAccessor(obj, obj.id))
            for permission in (READ_USER, UPDATE_USER):
                d.addCallback(addCapability, permission)
            d.addCallback(lambda ignore: obj)
            return d

        d = self._checkForUniqueUser(*a, **k)
        d.addCallback(createUser)
        d.addCallback(addCapabilities)
        return d

    def _checkForUniqueUser(self, *a, **k):
        """Check that the new user does not match an existing user"""
        username = k['username']
        openid = k['openid']

        # Crude load all the users until there is a user table
        d = self.findMany()

        def _( users, username, openid ):
            for user in users:
                if username and user.username == username:
                    raise UserExistsError( 'Duplicate user' )
                if openid and user.openid == openid:
                    raise UserExistsError( 'Duplicate user' )
        d.addCallback(_, username, openid)
        return d
        
    def findById(self, id):
        """Find a user by id.
        """
        def itemFound(item):
            if item is not None and item.testPermission(item.find):
                return item
            else:
                raise objstore.NotFound()
            
        d = self.sess.getItemById(id).addCallback(self.sess.capCtx.getProxy)
        d.addCallback(itemFound)
        return d

    @defer.deferredGenerator
    def findMany(self):
        """Find and return 0 or more users.
        """
        d = defer.waitForDeferred(self.sess.getItems(User))
        yield d
        items = d.getResult()
        result = []
        for item in items:
            d = defer.waitForDeferred(self.sess.capCtx.getProxy(item))
            yield d
            item = d.getResult()
            if item.testPermission(item.find):
                result.append(item)
        yield result
        
    def removeUser(self, id):
        """Remove a user from the system.
        
        user:
            a User instance or an integer ID.
        """
        def removeUser(user):
            d = user.delete(self.sess)
            d.addCallback(lambda ignore: user)
            return d

        def removeCapabilities(user):
            # remove capabilities referring to the deleted user
            d = self.sess.capCtx.deleteCapabilitiesForId(user.id)
            d.addCallback(lambda ignore: user)
            return d

        d = self.findById(id)
        d.addCallback(removeUser)
        d.addCallback(removeCapabilities)
        return d
    
    
class UsernamePasswordChecker(object):
    """A cred username/password checker that checks the credentials of User
    instances in the store.
    """
    implements( checkers.ICredentialsChecker )
    credentialInterfaces = [credentials.IUsernamePassword]
    
    def __init__(self, realm):
        self.realm = realm
    
    def requestAvatarId(self, credentials):
        """Check the username/password credentials against the User and
        return an avatar id (i.e. a user id).
        """
        return avatarIdForUsernamePassword(
            self.realm,
            credentials.username,
            credentials.password
            )
        
        
class TestingChecker(object):
    """Cred checker that uses username, password credentials in the config
    to automatically login.
    """
    implements( checkers.ICredentialsChecker )
    credentialInterfaces = [credentials.IAnonymous]
    
    def __init__(self, realm):
        self.realm = realm
    
    def requestAvatarId(self, credentials):
        configCreds = self.realm.config.get('testing', {}).get('adminCredentials')
        if configCreds is None:
            raise error.UnauthorizedLogin()
        username, password = configCreds
        return avatarIdForUsernamePassword(self.realm, username, password)

        
def avatarIdForUsernamePassword(realm, username, password):
    """Return the avatar id (i.e. the user's id) for the user with the
    given username and password.
    """

    def sessionStarted(sess):
        d = sess.getItems(
            User,
            where="username=%(username)s and password=%(password)s",
            params={'username':username, 'password':password}
            )
        d.addCallback(gotItems)
        d.addBoth(cleanup, sess)
        return d
    
    def gotItems(users):
        # Generators, schmenerators
        users = list(users)
        # There can be only one
        if len(users) != 1:
            raise error.UnauthorizedLogin()
        user = users[0]
        # Check the account has not been suspended
        if user.suspended:
            raise error.UnauthorizedLogin()
        # Looks good
        return user.id
    
    def cleanup(r, sess):
        d = sess.close()
        d.addCallback(lambda ignore: r)
        return d
        
    d = realm.store.startSession()
    d.addCallback(sessionStarted)
    return d
    
