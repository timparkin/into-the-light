"""Base content type code.

A content type is something that subclasses ContentItem and registers a plugin
of type 'cms/content-type'.

ContentItem has a "magic" class attribute called ''attributes'' that lists
the attributes of instances. A subclass's ''attributes'' are appended to all
those of the base class; there is no need to .append to the list.
"""

import datetime
from zope.interface import implements
from twisted.cred import portal
from twisted.internet import defer
from twisted.python.components import registerAdapter
from nevow import inevow, tags as T, url
import formal as forms
from poop import objstore
from crux import icrux

from tub.capabilities import CommonPermissions, GroupPermission
from tub.capabilities import UnauthorizedException, requiredPermissions
from tub.web import categorieswidget, util

from cms import icms


class Attribute(object):
    """Content item attribute.
    """
    def __init__(self, name, type, translatable=False, widgetFactory=None,classes=[]):
        self.name = name
        self.type = type
        self.translatable = translatable
        self.widgetFactory = widgetFactory
        self.classes=classes


class ContentItem(objstore.Item):
    """Content item base class.
    """
    implements(icms.IContentItem)

    __table__ = 'content_item'
    name = objstore.column()
    author = objstore.column('author')
    publicationDate = objstore.column('publication_date')
    expirationDate = objstore.column('expiration_date')
    workflowStatus = objstore.column('workflow_status')
    categories = objstore.column()

    attributes = [
        Attribute('name', forms.String(required=True)),
    ]

    systemAttributes = [
        Attribute('publicationDate', forms.Date(required=True), translatable=False, widgetFactory=forms.widgetFactory(forms.DatePartsInput,dayFirst=True)),
        Attribute('expirationDate', forms.Date(), translatable=False, widgetFactory=forms.widgetFactory(forms.DatePartsInput,dayFirst=True)),
        Attribute('metaKeywords', forms.String(), translatable=True),
        Attribute('metaDescription', forms.String(), translatable=True),
        Attribute('titleTag', forms.String(), translatable=True),
    ]

    categoriesAttributes = [
        Attribute('categories', forms.Sequence(), translatable=False, widgetFactory=categorieswidget.CheckboxTreeMultichoice )
    ]

    extraDataAttributes = [
        Attribute('extraData', forms.String(), translatable=False, widgetFactory=forms.TextArea )
    ]

    WORKFLOW_STATUS_EDITING = 0
    WORKFLOW_STATUS_WAITING = 1
    WORKFLOW_STATUS_APPROVED = 2
    WORKFLOW_STATUS_REVOKED = 3

    def __init__(self, session, id, name, author):
        super(ContentItem, self).__init__(session, id)
        self.name = name
        self.author = author
        self.publicationDate = datetime.datetime.utcnow().date()
        self.expirationDate = None
        self.workflowStatus = ContentItem.WORKFLOW_STATUS_EDITING
        self.categories = None
        self.extraData = None

        #workflow should be moved.
        self.workflowStatus = ContentItem.WORKFLOW_STATUS_EDITING

    def isComplete(self):
        """
        Test that all required attributes have been entered.

        As long as an attribute has been specified for at least one language it
        is considered entered.
        """
        def requiredAttrs():
            """Generator that yields the required attributes."""
            for attr in self.attributes:
                if [v for v in attr.type.validators if isinstance(v, forms.RequiredValidator)]:
                    yield attr
        for attr in requiredAttrs():
            # Get the value. This depends on translableness.
            if attr.translatable:
                value = getattr(self, attr.name, {})
            else:
                value = getattr(self, attr.name, None)
            # Test the value
            if value is None:
                return False
        # Got through, so it should be ok.
        return True

    def _initNewVersion(self):
        self.workflowStatus = ContentItem.WORKFLOW_STATUS_EDITING

    def _getAttributes(cls, whichAttributes):
        """Build a list of editable attributes for the editable type.

        The class hierarchy (well, mro really) is walked collecting attributes
        in the ''attributes'' class attr. The attributes are returned in the
        order they are listed, with the base-est class's attributes first.
        """

        l = []
        for attributes in [getattr(c, whichAttributes) for c in cls.__mro__ if hasattr(c, whichAttributes)][::-1]:
            for attribute in attributes:
                if attribute not in l:
                    l.append(attribute)
        return l
    _getAttributes = classmethod(_getAttributes)

    def _getAttributeValues(self, language, attributes, fallbackLanguages=None, returnLanguages=False):
        """Get all attributes for the specified language. If no value is found
        for an attribute then search the fallbackLanguages.
        """
        d = {}
        l = {}
        for attr in attributes:
            if not attr.translatable:
                val = getattr(self, attr.name, None)
                lang = None
            else:
                lang = language
                vals = getattr(self, attr.name, {})
                val = vals.get(language,None)
                if val is None and fallbackLanguages:
                    for fallbackLanguage in fallbackLanguages:
                        val = vals.get(fallbackLanguage)
                        if val is not None:
                            lang = fallbackLanguage
                            break
            d[attr.name] = val
            l[attr.name] = lang
        if returnLanguages:
            return d, l
        else:
            return d

    def _setAttributeValues(self, sess, language, attributes, **kw):
        """Set attributes in the kw dict on the content item. Attributes that
        are translatable should be stored as a dict with the language as the
        key.
        """
        for attr in attributes:
            if attr.name not in kw:
                continue
            if attr.translatable:
                val = getattr(self, attr.name, {})
                val[language] = kw.get(attr.name)
            else:
                val = kw.get(attr.name)
            setattr(self, attr.name, val)
        self.touch()

    def getAttributes(cls):
        return cls._getAttributes('attributes')
    getAttributes = classmethod(getAttributes)

    def getAttributeValues(self, language, fallbackLanguages=None, returnLanguages=False):
        return self._getAttributeValues(language, self.getAttributes(), fallbackLanguages, returnLanguages)

    def getAttributeValue(self, name, language, fallbackLanguages=None, returnLanguages=False):
        return self._getAttributeValues(language, self.getAttributes(), fallbackLanguages, returnLanguages).get(name,None)

    def setAttributeValues(self, sess, language, **kw):
        self._checkEditable()
        self._setAttributeValues(sess, language, self.getAttributes(), **kw)

    def getSystemAttributes(cls):
        return cls._getAttributes('systemAttributes')
    getSystemAttributes = classmethod(getSystemAttributes)

    def getSystemAttributeValues(self, language, fallbackLanguages=None, returnLanguages=False):
        return self._getAttributeValues(language, self.getSystemAttributes(), fallbackLanguages, returnLanguages)

    def getSystemAttributeValue(self, name, language, fallbackLanguages=None, returnLanguages=False):
        return self._getAttributeValues(language, self.getSystemAttributes(), fallbackLanguages, returnLanguages)[name]

    def setSystemAttributeValues(self, sess, language, **kw):
        self._checkEditable()
        self._setAttributeValues(sess, language, self.getSystemAttributes(), **kw)

    def getCategoriesAttributes(cls):
        return cls._getAttributes('categoriesAttributes')
    getCategoriesAttributes = classmethod(getCategoriesAttributes)

    def getCategoriesAttributeValues(self, language, fallbackLanguages=None, returnLanguages=False):
        return self._getAttributeValues(language, self.getCategoriesAttributes(), fallbackLanguages, returnLanguages)

    def setCategoriesAttributeValues(self, sess, language, **kw):
        self._checkEditable()
        self._setAttributeValues(sess, language, self.getCategoriesAttributes(), **kw)

    def getExtraDataAttributes(cls):
        return cls._getAttributes('extraDataAttributes')
    getExtraDataAttributes = classmethod(getExtraDataAttributes)

    def getExtraDataAttributeValues(self, language, fallbackLanguages=None, returnLanguages=False):
        return self._getAttributeValues(language, self.getExtraDataAttributes(), fallbackLanguages, returnLanguages)

    def getExtraDataAttributeValue(self, name, language, fallbackLanguages=None, returnLanguages=False):
        return self._getAttributeValues(language, self.getExtraDataAttributes(), fallbackLanguages, returnLanguages)[name]

    def setExtraDataAttributeValues(self, sess, language, **kw):
        self._checkEditable()
        self._setAttributeValues(sess, language, self.getExtraDataAttributes(), **kw)

    def setWorkflowEditing(self):
        self.workflowStatus = ContentItem.WORKFLOW_STATUS_EDITING
        self.touch()
        return defer.succeed(None)

    def setWorkflowWaiting(self):
        self._checkEditable()
        self.workflowStatus = ContentItem.WORKFLOW_STATUS_WAITING
        self.touch()
        return defer.succeed(None)

    def setWorkflowApproved(self):
        if self.workflowStatus == ContentItem.WORKFLOW_STATUS_REVOKED:
            raise ItemApprovedException()
        self.workflowStatus = ContentItem.WORKFLOW_STATUS_APPROVED
        self.touch()
        return self._revokeOldVersion()

    def setWorkflowRevoked(self):
        if self.workflowStatus != ContentItem.WORKFLOW_STATUS_APPROVED:
            raise ItemNotApprovedException()
        self.workflowStatus = ContentItem.WORKFLOW_STATUS_REVOKED
        self.touch()
        return defer.succeed(None)

    def _checkEditable(self):
        if self.workflowStatus in [ContentItem.WORKFLOW_STATUS_APPROVED,ContentItem.WORKFLOW_STATUS_REVOKED]:
            raise ItemApprovedException()

    def _revokeOldVersion(self):
        """Revoke the previous version of this item so this one is the only
        version that is approved.
        """
        # Return success immedatiately if there is no earlier version.
        if self.version == 1:
            return defer.succeed(None)

        def gotItem(item):
            item.workflowStatus = ContentItem.WORKFLOW_STATUS_REVOKED
            item.touch()

        d = self.session.getItemById(self.id, version=self.version-1, itemType=ContentItem)
        d.addCallback(gotItem)
        return d


NOTFOUND = object()


class LocalizedValue(object):
    """
    A localized attribute value along with its language and the direction the
    language should be rendered in.

    I can be renderer (wrongly - it's for backwards compatability) and I can
    also be asked for attributes using nevow's data directive so page templates
    can correctly decide how to render my value.
    """
    implements(inevow.IContainer, inevow.IRenderer)

    def __init__(self, value, dir, lang):
        self.value = value
        self.dir = dir
        self.lang = lang

    def child(self, ctx, name):
        if name not in ['value', 'dir', 'lang']:
            raise AttributeError()
        return getattr(self, name)

    def rend(self, ctx, data):
        return T.span(class_=self.dir)[T.xml(self.value)]


class ContentItemContainer(object):
    """inevow.IContainer adapter for ContentItem instances.

    This adapter will automatically retrieve the localised content of
    translatable attributes. Other attributes will be returned as it.
    """
    implements( inevow.IContainer )

    def __init__(self, original):
        self.original = original

    def child(self, ctx, name):

        # Attribute names should be strings not unicode
        # (unicode can happen if the data is requested directly from a template)
        name = str(name)

        # XXX hack!
        if name == 'childLink':
            return url.URL.fromContext(ctx).child(self.original.id)
        elif name == 'id':
            return self.original.id

        realm = util.getAvatar(ctx).realm
        try:
            language = inevow.ILanguages(ctx)[0]
        except IndexError:
            language = realm.defaultLanguage

        # We need to look through normal and system attributes
        funcs = [self.original.getAttributeValues, self.original.getSystemAttributeValues]
        for func in funcs:
            # Get the attributes and the language found for each attribute
            data, attrLangs = func(language, realm.fallbackLanguages, True)
            # No data, try next func
            data = data.get(name, NOTFOUND)
            if data is not NOTFOUND:
                break
        else:
            raise KeyError('Attribute %r missing' % name)

        # Get the language found for the attribute
        lang = attrLangs.get(name)

        # Return data now if not translatable
        if lang is None:
            return data

        # We have a language, create a localised value
        for l in realm.languages:
            if lang == l.code and l.publiccssclass:
                return LocalizedValue(data, l.publiccssclass, lang)

        raise Exception('Error creating localised value for attribute %r, ' \
                'language %r' % (name, lang))


registerAdapter(ContentItemContainer, icms.IContentItem, inevow.IContainer)


class ItemRow(object):
    def __init__(self, id, version, publicationDate, expirationDate, workflowStatus):
        self.id = int(id)
        self.version = int(version)
        self.publicationDate = publicationDate
        self.expirationDate = expirationDate
        self.workflowStatus = int(workflowStatus)

class ContentManager( object ):
    def __init__( self, avatar, application ):
        self.avatar = avatar
        self.application = application

    def createItem(self, sess, plugin, *a, **kw):
        def initializeObject(obj):
            obj.setWorkflowEditing()
            return obj

        def addCapabilities(obj):
            def addCapability(accessor, permission):
                d = accessor.addCapability(permission)
                d.addCallback(lambda ignore: accessor)
                return d

            # add capabilities to the creating user
            d = sess.capCtx.getCapabilityAccessor(obj)
            for permission in (CommonPermissions.READ, CommonPermissions.UPDATE):
                d.addCallback(addCapability, permission)
            d.addCallback(lambda ignore: obj)
            return d

        d = sess.createItem(plugin.contentItemFactory, *a, **kw)
        d.addCallback(initializeObject)
        d.addCallback(addCapabilities)
        return d

    def createNewVersion(self, sess, obj):
        def initializeObject(obj):
            obj._initNewVersion()
            return obj
        if not obj.testPermission(obj.setAttributeValues):
            raise UnauthorizedException(obj.subjectId, 'permission', obj.id)
        d = defer.maybeDeferred(sess.createNewVersion, obj.protectedObject)
        d.addCallback(initializeObject)
        return d

    def removeItem(self, sess, id):
        d = sess.getItemById(id)
        d.addCallback(self._removeItem, sess)
        d.addCallback(lambda ignore: sess.capCtx.deleteCapabilitiesForId(id))
        return d

    def _removeItem( self, item, sess ):
        plugin = self.application.contentTypes.getTypeForItem(item)
        d = plugin.removeItem( sess, item.id )
        return d

    def _getPublicallyVisibleVersion(self, rows):
        now = datetime.datetime.utcnow().date()
        for row in rows:
            if row.workflowStatus == ContentItem.WORKFLOW_STATUS_REVOKED:
                return None
            if row.workflowStatus != ContentItem.WORKFLOW_STATUS_APPROVED:
                continue
            if row.publicationDate and now < row.publicationDate:
                return None
            if row.expirationDate and now > row.expirationDate:
                return None
            return row
        return None

    def publicFindById(self, sess, id):
        """Find the public visible version of an it"""

        def gotRows(rows):
            rows = [ItemRow(*row[0:5]) for row in rows]
            visibleVersion = self._getPublicallyVisibleVersion(rows)
            if visibleVersion is None:
                return defer.succeed(None)
            return self.findById(sess, visibleVersion.id, visibleVersion.version)

        d = sess.curs.execute('select id, version, publication_date, expiration_date, workflow_status from content_item where id=%s order by version desc', (id,))
        d.addCallback(lambda ignore: sess.curs.fetchall())
        d.addCallback(gotRows)

        return d

    def findById(self, sess, id, version=None):

        d = sess.getItemById(id, version)
        d.addCallback( lambda item : sess.capCtx.getProxy( item ) )
        d.addCallback( self._filterItemBasedOnPermissions, sess )
        return d

    @defer.deferredGenerator
    def _filterItemBasedOnPermissions(self, item, sess):

        if not hasattr(item, 'findItem'):
            # don't know what to check so let it through
            yield item
        if item.testPermission(item.findItem):
            yield item
        else:
            yield None

    def publicFindManyContentItems(self, sess, itemType=None, where=None, params=None, orderBy=None):

        if itemType is None:
            itemType = ContentItem

        def getItem(rows):
            visibleVersion = self._getPublicallyVisibleVersion(rows)
            if visibleVersion is not None:
                return self.findById(sess, visibleVersion.id, visibleVersion.version)
            return None

        @defer.deferredGenerator
        def gotRows(rows):
            rv = []
            id = None
            testRows = []
            for row in rows:
                tmp = ItemRow(*row[0:5])
                if tmp.id != id:
                    d = getItem(testRows)
                    if d:
                        d = defer.waitForDeferred(d)
                        yield d
                        rv.append(d.getResult())
                    testRows = [tmp]
                    id = tmp.id
                testRows.append(tmp)
            d = getItem(testRows)
            if d:
                d = defer.waitForDeferred(d)
                yield d
                rv.append(d.getResult())
            yield rv

        sql = """select c.id, c.version, c.publication_date, c.expiration_date, c.workflow_status
                from item i join content_item c using (id, version) where i.type in (%(types)s)"""
        if where is not None:
            sql += ' and '
            sql += where
        sql += """ order by c.id desc, c.version desc"""
        types = tuple([cls.__typename__ for cls in sess.store.registry.typesFrom(itemType)])
        if params is None:
            params = {}
        params.update({'types':types})
        d = sess.curs.execute(sql, params)
        d.addCallback(lambda ignore: sess.curs.fetchall())
        d.addCallback(gotRows)
        return d

    def findMany( self, sess, itemType=ContentItem, filter=None, where=None, params=None ):

        d = sess.getItems( itemType, where=where, params=params )
        d.addCallback( self._filterItemsBasedOnPermissions, sess )
        d.addCallback( self._filterBasedOnFilter, filter )

        return d

    @defer.deferredGenerator
    def _filterItemsBasedOnPermissions( self, items, sess ):

        rv = []

        for item in items:
            d = defer.maybeDeferred(sess.capCtx.getProxy, item)
            d = defer.waitForDeferred(d)
            yield d
            item = d.getResult()

            if not hasattr(item, 'findItem'):
                # don't know what to check so skip it
                continue
            else:
                if item.testPermission(item.findItem):
                    rv.append( item )
        yield rv

    def _filterBasedOnFilter( self, items, filter ):
        return items

    def getNamesOfItems(self, sess):
        sql = """select c.id, c.name
                from content_item c 
                where c.version = (
                    select max(latest.version) 
                    from content_item latest 
                    where latest.id = c.id)"""
        d = sess.curs.execute(sql)
        d.addCallback(lambda ignore: sess.curs.fetchall())
        return d

def getClassName( c ):
    return '%s.%s' % (c.__module__, c.__name__)


def populateFormFromPlugin(form, plugin, immutable=False, immutableName=False):
    for attr in plugin.contentItemClass.getAttributes():
        if attr.name == 'name' and immutableName==True and 'Page' in plugin.name:
            attr.type.immutable = True
        else:
            attr.type.immutable = immutable
        cssClass=None
        tempClassList=[]
        if attr.translatable:
            tempClassList.append('translatable')
        if attr.classes:
            tempClassList.extend(attr.classes)
        if tempClassList!=[]:
            cssClass=' '.join(tempClassList)
        form.addField(attr.name, attr.type, widgetFactory=attr.widgetFactory, cssClass=cssClass)

class DefaultContentEditor(object):
    implements( icms.IContentEditor )

    def __init__(self, original):
        self.original = original

    def getForm(self, ctx, language, plugin, immutable):
        f = forms.Form()
        avatar = icrux.IAvatar(ctx)
        immutableName = avatar.realm.applications.applicationByName('content').isManagingSitemap()
        populateFormFromPlugin(f, plugin, immutable, immutableName=immutableName)
        f.data = self.original.getAttributeValues(language)
        return f

    def saveAttributes(self, ctx, form, data, language):
        sess = util.getStoreSession(ctx)
        d = defer.maybeDeferred( self.original.setAttributeValues, sess, language, **data )
        return d


##
# Metaclasses for easier setup
#

def capabilityWrapMethods(cls, capOId, methods):

    for method in methods:

        orig = getattr(cls, method)
        perms = []
        for cap in orig.groupCaps:
            perms.append(GroupPermission(cap, capOId))
        for cap in orig.otherCaps:
            perms.append(cap)
        setattr(cls, method, requiredPermissions(*perms)(orig))


class CMSMetaType(objstore.MetaItem):

    def __new__(mcls, name, bases, dct):
        cls = objstore.MetaItem.__new__(mcls, name, bases, dct)
        if dct.get('capabilityObjectId', None):
            mcls._wrapBasicMethods(cls)
        return cls

    def _wrapBasicMethods(mcls, cls):

        capOId = cls.capabilityObjectId
        methods = [ 'setAttributeValues',
            'setCategoriesAttributeValues',
            'setExtraDataAttributeValues',
            'setSystemAttributeValues',
            'setWorkflowEditing',
            'setWorkflowWaiting',
            'setWorkflowApproved',
            'setWorkflowRevoked',
            'findItem' ]

        capabilityWrapMethods(cls, capOId, methods)

    _wrapBasicMethods = classmethod(_wrapBasicMethods)


class CMSBase(ContentItem):

    __metaclass__ = CMSMetaType

    def setAttributeValues(self, sess, language, **kw):
        return ContentItem.setAttributeValues(self, sess, language, **kw)
    setAttributeValues.groupCaps = CommonPermissions.UPDATE,
    setAttributeValues.otherCaps = CommonPermissions.UPDATE,

    def setCategoriesAttributeValues(self, sess, language, **kw):
        return ContentItem.setCategoriesAttributeValues(self, sess, language, **kw)
    setCategoriesAttributeValues.groupCaps = CommonPermissions.UPDATE_CATEGORIES,
    setCategoriesAttributeValues.otherCaps = ()

    def setExtraDataAttributeValues(self, sess, language, **kw):
        return ContentItem.setExtraDataAttributeValues(self, sess, language, **kw)
    setExtraDataAttributeValues.groupCaps = CommonPermissions.UPDATE,
    setExtraDataAttributeValues.otherCaps = CommonPermissions.UPDATE,

    def setSystemAttributeValues(self, sess, language, **kw):
        return ContentItem.setSystemAttributeValues(self, sess, language, **kw)
    setSystemAttributeValues.groupCaps = CommonPermissions.UPDATE_METADATA,
    setSystemAttributeValues.otherCaps = ()

    def setWorkflowEditing(self):
        return ContentItem.setWorkflowEditing(self)
    setWorkflowEditing.groupCaps = CommonPermissions.UPDATE,
    setWorkflowEditing.otherCaps = CommonPermissions.UPDATE,

    def setWorkflowWaiting(self):
        return ContentItem.setWorkflowWaiting(self)
    setWorkflowWaiting.groupCaps = CommonPermissions.UPDATE,
    setWorkflowWaiting.otherCaps = CommonPermissions.UPDATE,

    def setWorkflowApproved(self):
        return ContentItem.setWorkflowApproved(self)
    setWorkflowApproved.groupCaps = CommonPermissions.APPROVE,
    setWorkflowApproved.otherCaps = ()

    def setWorkflowRevoked(self):
        return ContentItem.setWorkflowRevoked(self)
    setWorkflowRevoked.groupCaps = CommonPermissions.REVOKE,
    setWorkflowRevoked.otherCaps = ()

    def findItem( self, sess, item ):
        return item
    findItem.groupCaps = CommonPermissions.READ,
    findItem.otherCaps = CommonPermissions.READ,
    

class CMSPluginMetaType(type):

    def __new__(mcls, name, bases, dct):
        cls = type.__new__(mcls, name, bases, dct)
        return cls

    def __new__(mcls, name, bases, dct):
        cls = type.__new__(mcls, name, bases, dct)
        if dct.get('id', None):
            mcls._wrapBasicMethods(cls)
            cls.contentItemFactory = cls._create

        return cls

    def _wrapBasicMethods(mcls, cls):

        capOId = cls.id
        methods = ['_create', 'removeItem']

        capabilityWrapMethods(cls, capOId, methods)

    _wrapBasicMethods = classmethod(_wrapBasicMethods)


class CMSPluginBase(object):

    __metaclass__ = CMSPluginMetaType
    templates = None
    listable = False
    listTemplates = []

    def __init__(self):
        self.contentItemClass.plugin = self
    
    def _adapters(self):
        return [
            (DefaultContentEditor, self.contentItemClass, icms.IContentEditor)
        ]

    _adapters = property(_adapters)

    def initialize(self, realm):
        realm.store.registerType(self.contentItemClass)
        for a, o, i in self._adapters:
            registerAdapter(a, o, i)

    def _create( self, sess, id, name, *a, **kw ):
        return self.contentItemClass( sess, id, name, *a, **kw )
    _create.groupCaps = ()
    _create.otherCaps = CommonPermissions.CREATE,

    contentItemFactory = _create

    def removeItem( self, sess, id ):
        return sess.removeItem( id )
    removeItem.groupCaps = CommonPermissions.DELETE,
    removeItem.otherCaps = ()

    def setApplication(self, application):
        self.application = application

class PagishBase(CMSBase):
    isPagish=True

class PagishPluginMetaType(CMSPluginMetaType):
    pass

class PagishPluginBase(CMSPluginBase):
    pass

class NonPagishBase(CMSBase):
    isPagish=False

class NonPagishPluginMetaType(CMSPluginMetaType):
    pass

class NonPagishPluginBase(CMSPluginBase):
    pass

