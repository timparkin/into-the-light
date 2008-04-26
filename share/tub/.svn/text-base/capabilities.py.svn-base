from twisted.internet import defer
from zope.interface import implements, Interface

"""
* Subject: the object making the request
* Resource: the target object of a request
* Permission: the required permission to the resource
* Capability: The (Subject, Permission, Resource) combination
"""

class UnauthorizedException( Exception ):
    def __init__( self, subjectId, permission, resourceId ):
        
        message = "You don't have the permission."
#        message = permission.errorFormatter % dict( subject='You', description=permission.description, resource=resourceId )
#        print 'UnauthorizedException', message
        Exception.__init__( self, message )


def requiredPermissions( *permissions ):
    def _withPermissions( f ):
        def _( *a, **kw ):
            return f( *a, **kw )
        _.permissions = permissions
        return _
    return _withPermissions


class PermissionRegistry(dict):
    def register(self, permission):
        self[permission.name] = permission


permissionRegistry = PermissionRegistry()


class Permission( object ):
    """
        A permission should have a unique name.
        This is something like 'read' or 'write'
    """
    def __init__( self, name, description=None, errorFormatter=None ):
        self.name = name
        self.description = description
        if self.description == None:
            self.description = name
        self.errorFormatter = errorFormatter
        if self.errorFormatter == None:
            self.errorFormatter = "%(subject)s are not authorized to %(description)s %(resource)s" 
        permissionRegistry.register(self)

    def __repr__( self ):
        return "Permission( '%s' )" % self.name


class GroupPermission( object ):
    """
        This allows the specification of a permission as well as the specific
        resource id rather than it being derived from the context of a call.
    """
    def __init__( self, permission, resourceAlias ):
        self.permission = permission
        self.resourceAlias = resourceAlias
        self.name = self.permission.name
        self.description = self.permission.description
        self.errorFormatter = self.permission.errorFormatter

    def __repr__( self ):
        return 'GroupPermission( %s, %s )' % ( self.name, self.resourceAlias )


class PartialCapability( object ):
    """
        Internal to the capabilities. 
        Used to record the record the resourceId for a required permission.
    """
    def __init__( self, permission, resourceId ):
        self.permission = permission
        self.resourceId = resourceId
        self.name = self.permission.name
        self.description = self.permission.description
        self.errorFormatter = self.permission.errorFormatter

    def __repr__( self ):
        return 'PartialCapability( %s, %s )' % ( self.name, self.resourceId )


class CommonPermissions( object ):
    """
    Common, i.e. system-wide, permissions.
    """

    # Classic CRUD permissions.
    CREATE = Permission( 'common.group.create', 'create' )
    READ = Permission( 'common.group.read', 'read' )
    UPDATE = Permission( 'common.group.update', 'update' )
    DELETE = Permission( 'common.group.delete', 'delete' )

    # Workflow
    # XXX not sure these are common for Tub
    APPROVE = Permission( 'common.group.approve', 'approve' )
    REVOKE = Permission( 'common.group.revoke', 'revoke' )

    # XXX Hmm, are these really common at all?
    UPDATE_CATEGORIES = Permission( 'common.group.update_categories', 'update_categories' )
    UPDATE_CAPABILITIES = Permission( 'common.group.update_capabilities', 'update_capbilities' )
    UPDATE_METADATA = Permission( 'common.group.update_metadata', 'update_metadata' )
    UPDATE_SUSPENDED = Permission( 'common.group.update_suspended', 'suspended' )


class Capability( object ):
    """
        This brings together a subject, a permission and a resource.

        It is used to express 'fred can read pages', where 'fred' is the subject
        'read' is the permission and 'pages' is the resource.
    """
    def __init__( self, subjectId, name, resourceId ):
        self.subjectId = subjectId
        self.name = name
        self.resourceId = resourceId

    def __repr__( self ):
        return "Capability( %s, '%s', %s )" % ( self.subjectId, self.name, self.resourceId )

    def __eq__(self, other):
        if type(self) != type(other):
            return false
        return self.subjectId == other.subjectId\
                and self.name == other.name\
                and self.resourceId == other.resourceId


class ICapabilityContext( Interface ):

    def getProxy( self, item ):
        pass


class NullCapabilityContext( object ):
    """
        A 'null' capability context and checker, that says that you have access
        to everything
    """
    implements( ICapabilityContext )

    def __init__( self, sess, avatar ):
        self.sess = sess
        self.avatar = avatar

    def getProxy( self, item ):
        if isinstance( item, NullCapabilityProxy ):
            return item

        d = self.getCapabilityAccessor(item)
        d.addCallback(lambda ca: NullCapabilityProxy(item, ca))
        return d

    def _returnTrue( self, method ):
        return True

    def getCapabilityAccessor( self, item, subjectId=None ):
        return defer.succeed(NullCapabilityAccessor())

    def deleteCapabilitiesForId(self, id):
        return defer.succeed(None)


class NullCapabilityAccessor(object):

    def addCapability(self, permission):
        return defer.succeed(None)

    def removeCapability(self, permission):
        return defer.succeed(None)

    def testCapability(self, permission):
        return True


class EmptyCA( object ):
    def __init__( self ):
        self.capabilities = []


class RealCapabilityContext( object ):
    """
        The 'real' capability context and checker
    """

    implements( ICapabilityContext )

    def __init__( self, sess, avatar ):
        self.sess = sess
        self.avatar = avatar
        self._proxies = {}
        self._blankCA = EmptyCA()
        self._capabilityAccessors = {}

    def getProxy( self, item, blankProxy=False ):
        if isinstance( item, CapabilityProxy ):
            if self.subjectId == item.capabilityAccessor.subjectId:
                return item

        if item is None:
            return None
        proxy = self._proxies.get( item.id, None )
        if proxy is not None:
            return proxy
        if blankProxy is True:
            proxy = CapabilityProxy( item, self._blankCA )
            self._proxies[item.id] = proxy
            return proxy

        d = self.getCapabilityAccessor(item)

        def _( ca ):
            proxy = CapabilityProxy( item, ca )
            self._proxies[item.id] = proxy
            return proxy
        d.addCallback( _ )
        return d

    def getCapabilityAccessor( self, item, subjectId=None ):
        if subjectId is None:
            subjectId = self.subjectId
        key = (subjectId, item.id)
        rv = self._capabilityAccessors.get(key, None)
        if rv is not None:
            return defer.succeed(rv)

        ca = CapabilityAccessor( self.avatar, self.sess, subjectId, item.id, getattr( item, 'resourceIds', [] ) )
        self._capabilityAccessors[key] = ca
        d = ca.initialise()
        d.addCallback(lambda r : ca)
        return d

    def deleteCapabilitiesForId(self, id):
        sql = 'delete from capabilities where resource_id=%s or subject_id=%s'
        d = self.sess.curs.execute(sql, (id,id))
        return d


class CapabilityProxy( object ):
    def __init__( self, protectedObject, capabilityAccessor ):
        self.__dict__['_protectedObject'] = protectedObject
        self.__dict__['_subjectId'] = capabilityAccessor.subjectId
        self.__dict__['_capabilityAccessor'] = capabilityAccessor

    def getCapabilityAccessor(self):
        return self._capabilityAccessor
    capabilityAccessor = property(getCapabilityAccessor)

    def getSubjectId(self):
        return self._subjectId
    subjectId = property(getSubjectId)

    def getProtectedObject(self):
        return self._protectedObject
    protectedObject = property(getProtectedObject)

    def __getattr__(self, name):
        attr = getattr(self._protectedObject, name)

        # don't cache or test values
        if not callable(attr):
            return attr

        if self.testPermission(attr):
            setattr(self, name, attr)
        else:
            setattr(self, name, self._noAccess)
        return getattr(self, name)

    def __setattr__(self, name, value):
        setattr(self._protectedObject, name, value)

    def testPermission( self, attr ):

        if not callable( attr ):
            return True

        if attr == self._noAccess:
            return False

        requiredPermissions = getattr( attr, 'permissions', None )
        if requiredPermissions is None:
            return True
        requiredPermissions = self._convertPermissions( requiredPermissions, self._protectedObject.id )
        return self._testCapabilities( requiredPermissions )

    def _noAccess( self, *a, **kw ):
        raise UnauthorizedException( self.subjectId, 'permission', self._protectedObject.id )

    def _testCapabilities( self, requiredPermissions ):
        """
            Test against a list of permissions that I currently know about.
        """
        for p in requiredPermissions:
            for c in self.capabilityAccessor.capabilities:
                if c.resourceId == p.resourceId and c.name == p.name:
                    return True
        return False

    def _convertPermissions( self, permissions, resourceId ):
        rv = []
        for permission in permissions:
            if isinstance( permission, GroupPermission ):
                rv.append( PartialCapability( permission, permission.resourceId ) )
            else:
                rv.append( PartialCapability( permission, resourceId ) )
        return rv


class NullCapabilityProxy(object):

    def __init__(self, protectedObject, *a, **k):
        self.__dict__['_protectedObject'] = protectedObject

    def getProtectedObject(self):
        return self._protectedObject
    protectedObject = property(getProtectedObject)

    def __getattr__(self, name):
        return getattr(self._protectedObject, name)

    def __setattr__(self, name, value):
        setattr(self._protectedObject, name, value)

    def testPermission( self, attr ):
        return True


class CapabilityAccessor( object ):
    def __init__( self, avatar, sess, subjectId, resourceId, altResourceIds=None ):
        self._sess = sess
        self._avatar = avatar
        self.subjectId = subjectId
        self.resourceId = resourceId
        self.altResourceIds = altResourceIds
        if self.altResourceIds is None:
            self.altResourceIds = []
        self._capabilities = None

    def _getCapabilities( self ):
        if self._capabilities == None:
            raise Exception( 'CapabilityAccessor not initialised' )
        return self._capabilities

    capabilities = property( _getCapabilities )

    def initialise( self ):
        resourceIds = set()

        resourceIds.add( self.resourceId )

        [resourceIds.add( id ) for id in self.altResourceIds]
        
        sql = "select permission, resource_id from capabilities where subject_id = %s and resource_id in ( %s" + ', %s' * (len( resourceIds ) - 1) + " )"
        params = []
        params.append( self.subjectId )
        [ params.append( id ) for id in resourceIds ]
        d = self._sess.curs.execute( sql, tuple( params ) )
        d.addCallback(lambda ignore: self._sess.curs.fetchall())

        def _( rows ):
            self._capabilities = [ Capability( self.subjectId, row[0], row[1] ) for row in rows ]

        d.addCallback( _ )

        return d 

    def testCapability(self, permission):
        for capability in self._capabilities:
            if capability.name == permission.name:
                return True
        return False
        
    def addCapability(self, permission):
        """Give the current subject the permisson on the current resource.
        """
        sql = """
            insert into capabilities (subject_id, permission, resource_id, type)
            values (%s, %s, %s, %s)
            """
        capData = (self.subjectId, permission.name, self.resourceId, type)
        cap = Capability(*capData[:-1])
        if cap in self._capabilities:
            return defer.succeed(None)
        self._capabilities.append(cap)
        return self._sess.curs.execute(sql, capData)

    def removeCapability(self, permission):
        """Remove the permisson that the current subject has on the current resource.
        """
        sql = """
            delete from capabilities where subject_id=%s and permission=%s and
            resource_id=%s
            """
        capData = (self.subjectId, permission.name, self.resourceId)
        cap = Capability(*capData)
        self._capabilities.remove(cap)
        return self._sess.curs.execute(sql, capData)
        
