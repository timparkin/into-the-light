from zope.interface import implements
from datetime import datetime
from twisted.internet import defer
from twisted.internet.defer import returnValue
from twisted.python.components import registerAdapter
from nevow import inevow, url, tags as T
from poop.objstore import NotFound
from pollen.nevow.tabular import itabular, tabular, cellrenderers

from tub import capabilities
from tub.web import page, util, xforms
from sitemap import manager

from cms import contentitem, icms, fragment, fragmenttype
from cms.widgets import itemselection
import re

MSG_NOT_COMPLETE = 'Item is not complete enough to be approved.'


def loader(filename):
    """
    Load a template from this package's templates directory.
    """
    return util.PackageTemplate('cms.templates',
            filename, ignoreDocType=True)


class ContentItemTabularItem(object):

    directAttributes = ('author', 'id', 'workflowStatus', 'categories')

    def __init__(self, original):
        self.original = original

    def getAttributeValue(self, name):
        if name in self.directAttributes:
            return getattr(self.original, name)
        if name == 'plugin':
            return self.original.plugin.name
        return self.original.getAttributeValue(name, 'en')


registerAdapter(ContentItemTabularItem, contentitem.ContentItem, itabular.IItem)
registerAdapter(lambda x: x, ContentItemTabularItem, itabular.IItem)


class ContentItemsModel(object):
    implements(itabular.IModel)

    attributes = {
        'id': tabular.Attribute(),
        'name': tabular.Attribute(sortable=True),
        'editor': tabular.Attribute(),
        'author': tabular.Attribute(),
        'ctime': tabular.Attribute(sortable=True),
        'mtime': tabular.Attribute(),
        'plugin': tabular.Attribute(sortable=True),
        'title': tabular.Attribute(sortable=True),
        'type': tabular.Attribute(sortable=True),
        'workflowStatus': tabular.Attribute(sortable=True),
    }

    def __init__(self, storeSession, itemType, name=None, workflowStatus=None, listFacets=None, mask=None):
        self.storeSession = storeSession
        self.itemType = itemType
        self.name = name
        self.workflowStatus = workflowStatus
        self._items = None
        self.listFacets = listFacets or []
        self.mask = mask
        self.dir='asc'
        self.sort='ctime'
        self.pluginname = self.itemType.plugin.name
        if self.pluginname == 'Blog Entry':
            self.attributes['date'] = tabular.Attribute(sortable=True)

        for facet in self.listFacets:
            self.attributes[facet] = tabular.Attribute()

    def setOrder(self, name, dir):
        self.sort = name
        self.dir = dir


    def getItemCount(self):
        d = self._loadItems()
        d.addCallback(lambda items: len(items))
        return d

    def getItems(self, start, end):
        
        def offsetLimit(items):
            for item in items:
                item = itabular.IItem(item)
            items = map(itabular.IItem, items)
            comparator = lambda x, y: cmp(x.getAttributeValue(self.sort),
                    y.getAttributeValue(self.sort))
            reverse = (self.dir == 'desc')
            items = sorted(items, cmp=comparator, reverse=reverse)
            return items[start:end]
        d = self._loadItems()
        d.addCallback(offsetLimit)
        return d

    def _loadItems(self):
        """
        Load the items and cache them in an instance attribute.
        """
        if self._items is not None:
            return defer.succeed(self._items)
        def cacheAndReturn(items):
            filteredItems = []
            for item in items:
                if self.mask is None or self.mask not in item.plugin.name:
                    item.pluginname = item.plugin.name
                    filteredItems.append(item)
            self._items = filteredItems
            def c(f,s):
                if hasattr(f.plugin,'sort') and f.plugin.sort == 'date':
                    f.date = datetime.fromordinal( f.date.toordinal() )
                    s.date = datetime.fromordinal( s.date.toordinal() )
                    return cmp(f,s)
                else:
                    if hasattr(f.plugin,'sort'):
                        return cmp(getattr(f,f.plugin.sort,f.name), getattr(s,s.plugin.sort,s.name))
                    else:
                        return cmp(f.name, s.name)
            self._items.sort(c)
            return self._items
        where, params = self._sqlFragments()
        d = self.storeSession.getItems(self.itemType, 
            where=where, params=params)
        d.addCallback(cacheAndReturn)
        return d

    def _sqlFragments(self):
        sql = []
        params = {}
        if self.name:
            sql.append( " name like %(name)s" )
            params['name'] = self.name.replace('*', '%')
        if self.workflowStatus:
            sql.append( " workflow_status = %(workflowStatus)s" )
            params['workflowStatus'] = self.workflowStatus

        sql = ' and '.join(sql).strip()

        if not sql:
            return None, None
        else:
            return sql, params

class SitemappedItemsModel(object):
    implements(itabular.IModel)

    attributes = {
        'id': tabular.Attribute(),
        'name': tabular.Attribute(),
        'editor': tabular.Attribute(),
        'author': tabular.Attribute(),
        'ctime': tabular.Attribute(),
        'mtime': tabular.Attribute(),
        'title': tabular.Attribute(),
        'type': tabular.Attribute(),
        'workflowStatus': tabular.Attribute(),
    }

    def __init__(self, storeSession, itemType, name=None, workflowStatus=None, listFacets=None, application=None, avatar=None):
        self.storeSession = storeSession
        self.itemType = itemType
        self.name = name
        self.workflowStatus = workflowStatus
        self._items = None
        self.listFacets = listFacets or []
        self.application= application
        self.avatar=avatar

        for facet in self.listFacets:
            self.attributes[facet] = tabular.Attribute()

    def setOrder(self, attribute, ascending):
        pass

    def getItemCount(self):
        d = self._loadItems()
        d.addCallback(lambda items: len(items))
        return d

    def getItems(self, start, end):
        def offsetLimit(items):
            return items[start:end]
        d = self._loadItems()
        d.addCallback(offsetLimit)
        return d

    def _loadItems(self):
        """
        Load the items and cache them in an instance attribute.
        """
        if self._items is not None:
            return defer.succeed(self._items)
        def cacheAndReturn(items):
            self._items = list(items)
            return self._items
        where, params = self._sqlFragments()
        # I need to get the sitemap out here.

        def _getSiteMap(smm):
            return smm.loadSiteMap()

        def _getSiteMapItems(sitemap):
            def visitChildren(node,acc):
                for child in node.children:
                    acc.append(child)
                    visitChildren(child,acc)
                return acc
            acc = []
            if sitemap is None:
                return defer.succeed(acc)
            acc.append(sitemap)
            acc = visitChildren(sitemap,acc)
            return defer.succeed(acc)
        
        def _getContentItems(sitemapitems):
            ids = [item.itemId for item in sitemapitems]
            if ids == []:
                return defer.succeed([])
            else:
                return self.storeSession.getItemsByIds(ids)
            
        def _buildCompositeItems(sitemapitems,contentitems):
            contentitems = list(contentitems)
            cdict = {}
            for c in contentitems:
                cdict[c.id] = c
            items = []
            for n,item in enumerate(sitemapitems):
                s = sitemapitems[n]
                c = cdict[s.itemId]
                c.level = s.level
                c.label = s.label
                items.append(c)
            return defer.succeed(items)

        smm = self.application.sitemapManagerFactory(self.avatar,self.storeSession)
        d = _getSiteMap(smm).addCallback(
            lambda sitemap: _getSiteMapItems(sitemap).addCallback(
                lambda sitemapitems: _getContentItems(sitemapitems).addCallback(
                    lambda contentitems: _buildCompositeItems(sitemapitems,contentitems).addCallback(
                        lambda items: cacheAndReturn(items)
                    
            ))))
        return d
    
    def _sqlFragments(self):
        sql = []
        params = {}
        if self.name:
            sql.append( " name like %(name)s" )
            params['name'] = self.name.replace('*', '%')
        if self.workflowStatus:
            sql.append( " workflow_status = %(workflowStatus)s" )
            params['workflowStatus'] = self.workflowStatus

        sql = ' and '.join(sql).strip()

        if not sql:
            return None, None
        else:
            return sql, params
    

def pluginNameCellRenderer(tag,item,attribute):
    return tag.fillSlots('value', item.original.plugin.name)
    
class ContentItemsPage(xforms.ResourceMixin, page.Page):
    """The main content page.
    """
    componentContent = loader('ContentItemsPage.html')
    BASECONTENTTYPE = contentitem.NonPagishBase

    def __init__(self, avatar, application, type):
        xforms.ResourceMixin.__init__(self)
        page.Page.__init__(self)

        self.avatar = avatar
        self.application = application
        self.type = type

        setattr(self, 'child_system', application.services)


    def child__itemselector_(self, ctx):
        return itemselection.ItemSelectionResource(self.application)


    def child__action( self, ctx ):
        args = inevow.IRequest(ctx).args
        if 'delete' in args:
            return self._delete( ctx )

    def childFactory(self, ctx, name):

        # id may be encoded with a version e.g. id;version
        id,version = decodeIdVersion(name)

        def gotObject(obj):
            return icms.IEditableResourceFactory(obj).createEditableResource(
                    self.application, self.avatar)

        def catchNotFoundException(failure):
            failure.trap(NotFound)
            rv = self._cleanUpURL(url.URL.fromContext(ctx))
            return rv.replace('errormessage',
                'Item update failed. The item has been deleted.');

        sess = util.getStoreSession(ctx)
        d = self.application.getContentManager(
                self.avatar).findById(sess, id, version)
        d.addCallback(gotObject)
        d.addErrback(catchNotFoundException)
        return d

    def _delete(self, ctx):
        items = inevow.IRequest(ctx).args.get('item')
        if not items:
            return self._cleanUpURL(url.URL.fromContext(ctx))

        items = [int(i) for i in items]
        avatar = self.avatar
        sess = util.getStoreSession(ctx)

        def catchUnauthorizedException( failure, failures, id ):
            # Keep a note of which deletes failed
            failure.trap(capabilities.UnauthorizedException)
            failures.append(id)

        def catchNotFoundException(failure):
            # Item has been deleted already
            failure.trap(NotFound)

        @defer.deferredGenerator
        def removeItems(sess, avatar):


            def _getSiteMap(smm,node):
                sitemap = smm.loadSiteMap()
                return sitemap
            
            def _removeSiteMapNode(smm,sitemap,node):
                if node.getProtectedObject().isPagish:
                    childName = node.name.split('/')[-1]
                    sitemapnode = sitemap.findChildByName(childName)
                    if sitemapnode is not None:
                        return smm.removeNode(sitemapnode)

                return defer.succeed(False)
                
            def _removeContentItem(id):
                return self.application.getContentManager(self.avatar).removeItem(sess, id)
            
            failures = []
            smm = self.application.sitemapManagerFactory(avatar,sess)
            for id in items:
                d = self.application.getContentManager(self.avatar).findById(sess, id)
                d.addCallback( 
                    lambda node: _getSiteMap(smm,node).addCallback(
                        lambda sitemap: _removeSiteMapNode(smm,sitemap,node).addCallback(
                            lambda notNeeded: _removeContentItem(id)
                )))
                d.addErrback(catchUnauthorizedException, failures, id)
                d.addErrback(catchNotFoundException)
                d = defer.waitForDeferred(d)
                yield d
                d.getResult()
            d = defer.waitForDeferred(sess.flush())
            yield d
            try:
                d.getResult()
            except Exception, err:
                # This is about the best we can do to spot RI errors without
                # catching dbapi-specific exception types.
                print '>>>', err
                if str(err).find('violates foreign key') == -1 \
                    and str(err).find('content_item_sitemap_ri') == -1:
                    raise
                # I don't know which one caused the error so highlight all items
                failures = items

            yield failures

        def itemsRemoved(failures):

            # A bit ugly, how can it be improved?
            # Report the success or failure.
            if len( failures ) == 0:
                rv = self._cleanUpURL(url.URL.fromContext(ctx))
                return rv.replace('message', 'Items deleted successfully')
            if len( failures ) > 0:
                print '>> Reporting failures'
                message = "Delete failed. Either you do not have permission or items are referenced in navigation."

            # Set up the redirect to contain the message, and the items that
            # were selected so they will be still selected, also list the
            # items that failed.
            rv = self._cleanUpURL(url.URL.fromContext(ctx))
            rv = rv.replace('errormessage', message)
            for i in items:
                rv = rv.add( 'item', value=str( i ) )
            for i in failures:
                rv = rv.add( 'erroritem', value=str( i ) )

            # Some deletes failed so mark the transaction to be rolled back,
            # so none of the deletes are committed.
            sess.forceRollback = True

            print '>> bottom of items removed'
            return rv

        d = removeItems( sess, avatar )
        d.addCallback(itemsRemoved)
        return d



    def render_contentItems(self, ctx, data):
        perPage = int(inevow.IRequest(ctx).args.get('perPage', [20])[0])
        view = tabular.TabularView('items', data, perPage)
        view.columns.append(tabular.Column('id', '', 
            cellrenderers.CheckboxRenderer(name='item')))
        view.columns.append(tabular.Column('name', 'Name', 
            cellrenderers.LinkRenderer(url.URL.fromContext(ctx), 'id')))
        view.columns.append(tabular.Column('title', 'Title'))
        view.columns.append(tabular.Column('plugin', 'Type', cellrenderers.CallableCellRenderer(pluginNameCellRenderer)))
        view.columns.append(tabular.Column('author', 'Author'))
        view.columns.append(tabular.Column('workflowStatus', 'Status',
            cellrenderers.LookUpRenderer(EditContentPage.workflowStates)))
        view.columns.append(tabular.Column('date', 'Date'))
        for facet in self.application.listFacets:
            view.columns.append(tabular.Column(facet, facet, FacetRenderer()))
        return view

    def render_perPage(self,ctx,data):
        from nevow import tags as T
        options = ['20','50','100','300']
        wrapper = T.div(id='perPageOptions')
        wrapper['Item per Page: ']
        for option in options:
            wrapper[ T.a(href=url.gethere.replace('perPage',option))[ option ] ]
            wrapper[ ' ' ]
        return wrapper    
    
    def data_contentItems(self, ctx, data):
        args = inevow.IRequest(ctx).args

        name = args.get('name', [None])[0]
        workflowStatus = args.get('workflowStatus', [None])[0]

        storeSession = util.getStoreSession(ctx)
        if self.type is None:
            contentType = self.BASECONTENTTYPE
            mask = 'Fragment'
        else:
            contentType = self.type.contentItemClass
            mask = None
        return ContentItemsModel(storeSession, contentType, name, workflowStatus, self.application.listFacets, mask=mask)



                         
            

    @defer.inlineCallbacks
    def render_treetablemap(self,ctx,data):
        def getChildren(count, map, node):
            thisCount = count
            for child in node.children:
                map.append( str(thisCount) )
                count += 1
                getChildren(count, map, child)

        avatar = self.avatar
        sess = util.getStoreSession(ctx)
        smm = self.application.sitemapManagerFactory(avatar,sess)
        sitemap = yield smm.loadSiteMap()
        map = ['0']
        getChildren(1,map,sitemap)
        
        returnValue('var map=[%s];'%','.join(map))

    def render_contentItems_actions(self, ctx, data):
        return ctx.tag(action=url.URL.fromContext(ctx).child('_action'))

    def form_search(self, ctx):

        args = inevow.IRequest(ctx).args

        name = args.get('name', [None])[0]
        workflowStatus = args.get('workflowStatus', [None])[0]

        form = xforms.Form()
        form.addField('name', xforms.String())
        form.addField('workflowStatus', xforms.Integer(),
            widgetFactory=xforms.widgetFactory(xforms.SelectChoice, EditContentPage.workflowStates) )
        form.addAction(self._submit_search,'search')
        form.data = {'name':name, 'workflowStatus':workflowStatus}
        return form

    def _submit_search(self, ctx, form, data):

        u = url.URL.fromContext(ctx)
        u = u.replace('name', data['name'] )
        u = u.replace('workflowStatus', data['workflowStatus'] )
        return u 

    def _cleanUpURL(self, u):
        rv = u.remove('sort')
        rv = rv.remove('query')
        return rv


    # Start of the new content item section    
    def render_type(self,ctx,data):
        if self.type is not None:
            return self.type.name
        else:
            return 'Content Item'
        

    def form_newItem(self, ctx):
        form = xforms.Form(self.cbCreateItem)
        form.addField('itemName', xforms.String(required=True))
        if self.type is not None:
            form.addField('contentType', xforms.String(required=True), xforms.Hidden)
            form.data={'contentType': self.type.name}
        else:
            form.addField('contentType', xforms.String(required=True),
            xforms.widgetFactory(xforms.RadioChoice, options=self.data_types))
        form.addAction(self.cbCreateItem)
        return form

    def data_types(self, ctx, data):
        """
        Return a sequence of (typeName, typeDescription) tuples.
        """
        storeSession = util.getStoreSession(ctx)
        return accessibleContentTypes(storeSession, self.application.contentTypes, 'nonpagish')

    def cbCreateItem(self, ctx, form, data):
        """
        Form callback to create an item.

        Once the item is created, the browser is redirected to the edit page.
        """

        def getPluginByName(pluginName):
            sess = util.getStoreSession(ctx)
            return defer.succeed(self.application.contentTypes.get(pluginName))

        def createObject(contentPlugin, itemName):
            sess = util.getStoreSession(ctx)
            avatar = self.avatar
            d = self.application.getContentManager(self.avatar).createItem(sess,
                    contentPlugin, itemName, avatar.user.name)
            return d

        def objectCreated(obj):
            u = url.here.up().child(obj.id)
            return u.replace('message', 'Item added successfully')

        def errUnauthorized(failure):
            failure.trap(capabilities.UnauthorizedException)
            u = url.here
            return u.replace('errormessage', 'You do not have permission to create this item.')

        # Get the bits we need from the form data
        itemName = data['itemName']
        contentType = data['contentType']

        # Add the item
        d = getPluginByName(contentType)
        d.addCallback(createObject, itemName)
        d.addCallback(objectCreated)
        d.addErrback(errUnauthorized)
        return d


class FragmentsPage(ContentItemsPage):   


    def render_contentItems(self, ctx, data):
        view = tabular.TabularView('items', data, 20)
        view.columns.append(tabular.Column('id', '', 
            cellrenderers.CheckboxRenderer(name='item')))
        view.columns.append(tabular.Column('name', 'Name', 
            cellrenderers.LinkRenderer(url.URL.fromContext(ctx), 'id')))
        view.columns.append(tabular.Column('type', 'Type'))
        view.columns.append(tabular.Column('author', 'Author'))
        view.columns.append(tabular.Column('workflowStatus', 'Status',
            cellrenderers.LookUpRenderer(EditContentPage.workflowStates)))
        for facet in self.application.listFacets:
            view.columns.append(tabular.Column(facet, facet, FacetRenderer()))
        return view

    componentContent = loader('FragmentsPage.html')
    
    def __init__(self, avatar, application):
        ContentItemsPage.__init__(self, avatar, application, fragment.FragmentPlugin)
        
    @defer.inlineCallbacks
    def form_newItem(self, ctx):
        sess = util.getStoreSession(ctx)
        items = yield sess.getItems(fragmenttype.FragmentType)
        fragmentTypes = []
        for item in items:
            fragmentTypes.append( (item.name,item.description) )
        
        form = xforms.Form(self.cbCreateItem)
        form.addField('itemName', xforms.String(required=True))
        if len(fragmentTypes) == 0:
            form.addField('fragmentType', xforms.String(required=True), xforms.Hidden)
            form.data={'fragmentType': fragmentTypes[0]}
        else:
            form.addField('fragmentType', xforms.String(required=True),
            xforms.widgetFactory(xforms.RadioChoice, options=fragmentTypes))
        if self.type is not None:
            form.addField('contentType', xforms.String(required=True), xforms.Hidden)
            form.data={'contentType': self.type.name}
        else:
            form.addField('contentType', xforms.String(required=True),
            xforms.widgetFactory(xforms.RadioChoice, options=self.data_types))            
        form.addAction(self.cbCreateItem)
        returnValue(form)

    def cbCreateItem(self, ctx, form, data):
        """
        Form callback to create an item.

        Once the item is created, the browser is redirected to the edit page.
        """

        def getPluginByName(pluginName):
            sess = util.getStoreSession(ctx)
            return defer.succeed(self.application.contentTypes.get(pluginName))

        def createObject(contentPlugin, itemName):
            sess = util.getStoreSession(ctx)
            avatar = self.avatar
            d = self.application.getContentManager(self.avatar).createItem(sess,
                    contentPlugin, itemName, avatar.user.name)
            return d

        def objectCreated(obj, fragmentType):
            obj.type = fragmentType
            sess = util.getStoreSession(ctx)
            return sess.flush()
        
        def addedFragmentType(obj):
            u = url.here.child(obj.id)
            return u.replace('message', 'Item added successfully')

        def errUnauthorized(failure):
            failure.trap(capabilities.UnauthorizedException)
            u = url.here
            return u.replace('errormessage', 'You do not have permission to create this item.')

        # Get the bits we need from the form data
        itemName = data['itemName']
        contentType = data['contentType']
        fragmentType = data['fragmentType']

        # Add the item
        d = getPluginByName(contentType)
        d.addCallback(createObject, itemName)
        d.addCallback(lambda obj: objectCreated(obj, fragmentType).addCallback(
            lambda ignore: addedFragmentType(obj)
                      ))
        d.addErrback(errUnauthorized)
        return d        
        
        
class FragmentsTypesPage(ContentItemsPage):
    
    componentContent = loader('FragmentsTypesPage.html')
    
    def __init__(self, avatar, application):
        ContentItemsPage.__init__(self, avatar, application, fragmenttype.FragmentTypePlugin)

    def render_contentItems(self, ctx, data):
        view = tabular.TabularView('items', data, 20)
        view.columns.append(tabular.Column('id', '', 
            cellrenderers.CheckboxRenderer(name='item')))
        view.columns.append(tabular.Column('name', 'Name', 
            cellrenderers.LinkRenderer(url.URL.fromContext(ctx), 'id')))
        view.columns.append(tabular.Column('author', 'Author'))
        view.columns.append(tabular.Column('workflowStatus', 'Status',
            cellrenderers.LookUpRenderer(EditContentPage.workflowStates)))
        for facet in self.application.listFacets:
            view.columns.append(tabular.Column(facet, facet, FacetRenderer()))
        return view
        

def attrCellRenderer(tag,item,attributes):
    # TODO: This needs to spit out the Type Plugin Name if it's a type we want - also should it be using the item.original here? security?
    return tag.fillSlots('value', T.span(class_='clickedit',title='id %s %s'%(item.original.id,attributes))[ getattr(item.original,attributes,'')] )
   
class LinkRenderer(cellrenderers.CallableCellRenderer):

    def __init__(self, baseURL, idAttribute=None, default=None, pattern=None):
        cellrenderers.CallableCellRenderer.__init__(self, self.renderer, pattern=pattern)
        self.baseURL = baseURL
        self.idAttribute = idAttribute
        self.default = default or ' '

    def renderer(self, tag, item, attribute):

        value = item.getAttributeValue(attribute)
        if not value:
            value = self.default

        if self.idAttribute:
            id = item.getAttributeValue(self.idAttribute)
        else:
            id = item.getAttributeValue(attribute)

        if id:
            u = self.baseURL.child(id)
            tag.fillSlots('value', T.a(href=u)[value] )
        else:
            tag.fillSlots('value', value)

        return tag   
   
   
class InvalidNodes(Exception):
    pass

class MissingParentNode(Exception):
    pass

class NodeAlreadyExists(Exception):
    pass



class SitemappedItemsPage(ContentItemsPage):   

    componentContent = loader('SitemappedItemsPage.html')
    BASECONTENTTYPE = contentitem.PagishBase
    
    def __init__(self, avatar, application):
        ContentItemsPage.__init__(self, avatar, application, None)
  
    def child__action( self, ctx ):
        args = inevow.IRequest(ctx).args
        if 'delete' in args:
            return self._delete( ctx )
        if 'move' in args:
            return self._move( ctx )        
        if 'applyLabelAndLevel' in args:
            return self._applyLabelAndLevel( ctx )        
        if 'updateUrls' in args:
            return self._updateUrls( ctx )        
        if 'applychanges' in args:
            return self._applyChanges( ctx )

    def _delete(self, ctx):
        items = inevow.IRequest(ctx).args.get('item')
        if not items:
            return self._cleanUpURL(url.URL.fromContext(ctx))

        items = [int(i) for i in items]
        avatar = self.avatar
        sess = util.getStoreSession(ctx)

        def catchUnauthorizedException( failure, failures, id ):
            # Keep a note of which deletes failed
            failure.trap(capabilities.UnauthorizedException)
            failures.append(id)

        def catchNotFoundException(failure):
            # Item has been deleted already
            failure.trap(NotFound)

        @defer.deferredGenerator
        def removeItems(sess, avatar):


            def _getSiteMap(smm,node):
                sitemap = smm.loadSiteMap()
                return sitemap
            
            def _removeSiteMapNode(smm,sitemap,node):
                if node.getProtectedObject().isPagish:
                    childName = node.name.split('/')[-1]
                    sitemapnode = sitemap.findChildByName(childName)
                    if sitemapnode is not None:
                        return smm.removeNode(sitemapnode)

                return defer.succeed(False)
                
            def _removeContentItem(id):
                return self.application.getContentManager(self.avatar).removeItem(sess, id)
            
            failures = []
            smm = self.application.sitemapManagerFactory(avatar,sess)
            for id in items:
                d = self.application.getContentManager(self.avatar).findById(sess, id)
                d.addCallback( 
                    lambda node: _getSiteMap(smm,node).addCallback(
                        lambda sitemap: _removeSiteMapNode(smm,sitemap,node).addCallback(
                            lambda notNeeded: _removeContentItem(id)
                )))
                d.addErrback(catchUnauthorizedException, failures, id)
                d.addErrback(catchNotFoundException)
                d = defer.waitForDeferred(d)
                yield d
                d.getResult()
            d = defer.waitForDeferred(sess.flush())
            yield d
            try:
                d.getResult()
            except Exception, err:
                # This is about the best we can do to spot RI errors without
                # catching dbapi-specific exception types.
                print '>>>', err
                if str(err).find('violates foreign key') == -1 \
                    and str(err).find('content_item_sitemap_ri') == -1:
                    raise
                # I don't know which one caused the error so highlight all items
                failures = items

            yield failures

        def itemsRemoved(failures):

            # A bit ugly, how can it be improved?
            # Report the success or failure.
            if len( failures ) == 0:
                rv = self._cleanUpURL(url.URL.fromContext(ctx))
                return rv.replace('message', 'Items deleted successfully')
            if len( failures ) > 0:
                print '>> Reporting failures'
                message = "Delete failed. Either you do not have permission or items are referenced in navigation."

            # Set up the redirect to contain the message, and the items that
            # were selected so they will be still selected, also list the
            # items that failed.
            rv = self._cleanUpURL(url.URL.fromContext(ctx))
            rv = rv.replace('errormessage', message)
            for i in items:
                rv = rv.add( 'item', value=str( i ) )
            for i in failures:
                rv = rv.add( 'erroritem', value=str( i ) )

            # Some deletes failed so mark the transaction to be rolled back,
            # so none of the deletes are committed.
            sess.forceRollback = True

            print '>> bottom of items removed'
            return rv

        d = removeItems( sess, avatar )
        d.addCallback(itemsRemoved)
        return d


    
    @defer.inlineCallbacks
    def _applyChanges( self,ctx ):
        
        args = inevow.IRequest(ctx).args
        changes = {}
        for key, value in args.items():
            if key.startswith('tablefield'):
                null, attribute, id = key.split('-')
                try:
                    id = int(id)
                except ValueError:
                    rv = self._cleanUpURL(url.URL.fromContext(ctx))
                    rv = rv.replace('errormessage', 'invalid form, contact support')
                    yield rv        
                changes.setdefault(attribute,[]).append( (id,value) )
        for id, values in changes.get('label',[]):
            print 'applying label %s to item with id %s'%(values[1],id)
            yield self._processApplyLabelAndLevel( ctx, id, values[1], None )
        for id, values in changes.get('level',[]):
            print 'applying level %s to item with id %s'%(values[1],id)
            yield self._processApplyLabelAndLevel( ctx, id, None, values[1] )
        for id, values in changes.get('name',[]):
            print 'moving url %s to %s'%(values[0],values[1])
            yield self._processUpdateUrls( ctx, values[0], values[1] )
        try:
            for id, values in changes.get('move',[]):
                try:
                    amount = int(values[1])
                    id = int(id)
                    print 'moving node %s by %s'%(id, amount)
                    yield self._processMove( ctx, id, amount )
                except Exception, e:
                    rv = self._cleanUpURL(url.URL.fromContext(ctx))
                    rv = rv.replace('errormessage', e.message)
                    returnValue(rv)                    
                    
        except Exception, e:
            rv = self._cleanUpURL(url.URL.fromContext(ctx))
            rv = rv.replace('errormessage', e.message)
            returnValue(rv)        
            
        rv = self._cleanUpURL(url.URL.fromContext(ctx))
        rv.replace('message',  'Urls updated') 
        returnValue( rv)    
            
    
    def _updateUrls( self, ctx ):
        def _success():
            rv = self._cleanUpURL(url.URL.fromContext(ctx))
            return rv.replace('message',  'Urls updated')

        def _catchException(e):
            rv = self._cleanUpURL(url.URL.fromContext(ctx))
            rv = rv.replace('errormessage', 'problem updating urls %s'%e.message)
            return rv
        
        urlFrom = inevow.IRequest(ctx).args.get('from')[0]
        urlTo = inevow.IRequest(ctx).args.get('to')[0]          
        
        d = _processUpdateUrls( self, ctx, urlFrom, urlTo )
        d.addCallback(_success)
        d.addErrback(_catchException)
        return d


    @defer.inlineCallbacks
    def _processUpdateUrls( self, ctx, urlFrom, urlTo ):
        """ fancy stuff to move lots of content items somewhere else and handle sitemap refiddlification
        
         1, Check for clashes in names
         2, Update LTree table 
         3, Recalculate the 'ord' column
         4, update the names - load item, update name, touch
         
         
         1, only needs ltree table - can be done in sql
         2, only needs sql
         3, only needs sql
         4, needs content manager
         
        """
        
        def _getSiteMap(smm):
            return smm.loadSiteMap()
        
        def _checkForUrlClash(sitemap,urlFrom,urlTo):
            fromNode = sitemap.getNodeFromUrl(urlFrom)
            toNode = sitemap.getNodeFromUrl(urlTo)
            if fromNode is None:
                raise InvalidNodes('from node doesn\'t exist : fromNode %s, toNode %s'%(fromNode,toNode))
            if toNode is not None:
                raise InvalidNodes('to node exists : fromNode %s, toNode %s'%(fromNode,toNode))
                
        avatar = self.avatar
        sess = util.getStoreSession(ctx)
        smm = self.application.sitemapManagerFactory(avatar,sess)        

        # Get the Sitemap
        sitemap = yield _getSiteMap(smm)

        # 1. Check for Clashes
        _checkForUrlClash(sitemap,urlFrom,urlTo)

        # Update the Ltree Table
        yield sess.curs.execute('select id,path,textid,ord from sitemap')
        sitemapItems = yield sess.curs.fetchall()
        
        # 2. Relabel nodes
        for item in sitemapItems:
            urlFromLtreePath = 'root%s'%'.'.join(urlFrom.split('/'))
            urlToLtreePathPattern = 'root%s'%'.'.join(urlTo.split('/'))
            p = re.compile( '^%s'%urlFromLtreePath) 
            newPath = p.sub(urlToLtreePathPattern,item[1])
            
            if item[1] == urlFromLtreePath:
                # if we have an exact match, we need to update the textid
                sql = 'update sitemap set path=%s,textid=%s,ord=ord+10000 where id=%s'
                yield sess.curs.execute(sql,(newPath,urlTo.split('/')[-1],item[0]))
                
            elif item[1].startswith(urlFromLtreePath):
                # if the path startswith the pattern, then just update the path
                sql = 'update sitemap set path=%s where id=%s'
                yield sess.curs.execute(sql,(newPath,item[0]))
                
            yield sess.curs.execute('select item_id from sitemap_item, sitemap where sitemap_item.sitemap_id = sitemap.id and sitemap.id=%s',(item[0],))
            contentItemId = yield sess.curs.fetchall()
            contentItem = yield self.application.getContentManager(self.avatar).findById(sess, contentItemId[0][0])
            p = re.compile( '^%s'%urlFrom)
            contentItem.name = p.sub(urlTo,contentItem.name)
            contentItem.touch()

        # get the parent node of the urlTo and find all of it's children (i.e the targets
        parentpath = '.'.join(urlToLtreePathPattern.split('.')[:-1])
        sql = 'select id from sitemap where path~\'%s.*{1}\' order by ord'%parentpath
        yield sess.curs.execute(sql)
        itemChildren = yield sess.curs.fetchall()

        #3. Loop on all of the nodes found above and update the ord column with sequential numbers
        for n,child in enumerate(itemChildren):
            sql = 'update sitemap set ord=%s where id=%s'
            yield sess.curs.execute(sql,(n+1,child[0]))
                   
        returnValue(None)              
                

    def _applyLabelAndLevel( self, ctx ):
        
        def _success():
            rv = self._cleanUpURL(url.URL.fromContext(ctx))
            return rv.replace('message', 'Item label and level updated successfully')

        def _catchException(e):
            rv = self._cleanUpURL(url.URL.fromContext(ctx))
            rv = rv.replace('errormessage', 'problem updateing label or level for item')
            return rv
        
        args = inevow.IRequest(ctx).args
        items = args.get('item')
        if not items:
            return self._cleanUpURL(url.URL.fromContext(ctx))
        items = [int(i) for i in items]
        if len(items) > 1:
            return self._cleanUpURL(url.URL.fromContext(ctx))
        itemId = items[0]

        label = args.get('label')[0].strip()
        if label == '':
            label = None

        level = args.get('level')[0].strip()
        if level == '':
            level = None
        else:
            level = int(level)            
            
        d = self._processApplyLabelAndLevel(self,ctx, itemId, label, level)
        d.addCallback(_success)
        d.addErrback(_catchException)
        return d
        
    def _processApplyLabelAndLevel( self, ctx, itemId, label, level ):

        def _getSiteMap(smm):
            return smm.loadSiteMap()
    
        def _getItem(smm,itemId):
            return self.application.getContentManager(self.avatar).findById(sess, itemId)
        
        def _getSiteMapNode(sitemap,item):
            if item.name == '/':
                return defer.succeed(sitemap)
            else:
                return defer.succeed(sitemap.getNodeFromUrl(item.name))
        
        def _updateSiteMapNode(smm, siteMapNode, itemId, label, level):
            if label is None and level is not None:
                return smm.updateNode(siteMapNode, 'cms', itemId,level=level)
            if level is None and label is not None:
                return smm.updateNode(siteMapNode, 'cms', itemId,label=label)
            if label is not None and level is not None:
                return smm.updateNode(siteMapNode, 'cms', itemId,label=label,level=level)
            
        
        avatar = self.avatar
        sess = util.getStoreSession(ctx)
        smm = self.application.sitemapManagerFactory(avatar,sess)        
        
        d = _getSiteMap(smm).addCallback(
            lambda sitemap: _getItem(smm,itemId).addCallback(
                lambda item: _getSiteMapNode(sitemap,item).addCallback(
                    lambda siteMapNode: _updateSiteMapNode(smm,siteMapNode,itemId,label,level)
        )))

        return d
        
    def _move(self,ctx):        
        def _success():
            rv = self._cleanUpURL(url.URL.fromContext(ctx))
            return rv.replace('message', 'Item moved successfully')

        def _catchException(e):
            rv = self._cleanUpURL(url.URL.fromContext(ctx))
            rv = rv.replace('errormessage', 'problem moving item')
            return rv

        items = inevow.IRequest(ctx).args.get('item')
        if not items:
            return self._cleanUpURL(url.URL.fromContext(ctx))
        items = [int(i) for i in items]
        moveAmount = int(inevow.IRequest(ctx).args.get('moveAmount')[0])
        if len(items) > 1 or moveAmount == 0:
            return self._cleanUpURL(url.URL.fromContext(ctx))
        itemId = items[0]
        
        d = self._processMove(self,ctx,itemId,moveAmount)
        d.addCallback(_success)        
        d.addErrback(_catchException)
        return d
        
        
    def _processMove(self, ctx, itemId, moveAmount):
        print 'in mov', itemId, moveAmount

        def _getSiteMap(smm):
            return smm.loadSiteMap()
    
        def _getItem(smm,itemId):
            return self.application.getContentManager(self.avatar).findById(sess, itemId)
        
        def _getSiteMapNode(sitemap,item):
            return defer.succeed(sitemap.getNodeFromUrl(item.name))
        
        def _moveItemByAmount(smm, siteMapNode, amount):
            return smm.moveNodeByAmount(siteMapNode,amount)
            

        avatar = self.avatar
        sess = util.getStoreSession(ctx)
        smm = self.application.sitemapManagerFactory(avatar,sess)
        
        
        d = _getSiteMap(smm).addCallback(
            lambda sitemap: _getItem(smm,itemId).addCallback(
                lambda item: _getSiteMapNode(sitemap,item).addCallback(
                    lambda siteMapNode: _moveItemByAmount(smm,siteMapNode,moveAmount)
        )))
        return d
        
    def render_contentItems(self, ctx, data):
        view = tabular.TabularView('items', data, 20)
        view.columns.append(tabular.Column('id', '', 
            cellrenderers.CheckboxRenderer(name='item')))
        view.columns.append(tabular.Column('name', 'Name',cellrenderers.CallableCellRenderer(attrCellRenderer)))
        view.columns.append(tabular.Column('title', 'Title',LinkRenderer(url.URL.fromContext(ctx), 'id')))
        view.columns.append(tabular.Column('plugin', 'Type',cellrenderers.CallableCellRenderer(pluginNameCellRenderer)))
        view.columns.append(tabular.Column('author', 'Author'))
        view.columns.append(tabular.Column('label', 'Label',cellrenderers.CallableCellRenderer(attrCellRenderer)))
        view.columns.append(tabular.Column('level', 'Level',cellrenderers.CallableCellRenderer(attrCellRenderer)))      
        view.columns.append(tabular.Column('workflowStatus', 'Status',
            cellrenderers.LookUpRenderer(EditContentPage.workflowStates)))

        def nullCellRenderer(tag,item,attributes):
            # TODO: This needs to spit out the Type Plugin Name if it's a type we want - also should it be using the item.original here? security?
            return tag.fillSlots('value', T.span(class_='clickedit',title='id %s %s'%(item.original.id,attributes))[ 'move' ] )
        view.columns.append(tabular.Column('move', 'Move',cellrenderers.CallableCellRenderer(nullCellRenderer)))      
        
        for facet in self.application.listFacets:
            view.columns.append(tabular.Column(facet, facet, FacetRenderer()))
        return view        

    
    def data_contentItems(self, ctx, data):
        args = inevow.IRequest(ctx).args

        name = args.get('name', [None])[0]
        workflowStatus = args.get('workflowStatus', [None])[0]

        storeSession = util.getStoreSession(ctx)
        if self.type is None:
            contentType = self.BASECONTENTTYPE
        else:
            contentType = self.type.contentItemClass
        return SitemappedItemsModel(storeSession, contentType, name, workflowStatus, self.application.listFacets,self.application,self.avatar)    
    
    def form_newItem(self, ctx):
        form = xforms.Form(self.cbCreateItem)
        form.addField('itemName', xforms.String(required=True),label='url')
        form.addField('sitemapLabel', xforms.String(required=True),label='Label')
        form.addField('sitemapLevel', xforms.Integer(required=True),label='Level')
        form.addField('contentType', xforms.String(required=True),
        xforms.widgetFactory(xforms.RadioChoice, options=self.data_types))
        form.addAction(self.cbCreateItem)
        return form

    def data_types(self, ctx, data):
        """
        Return a sequence of (typeName, typeDescription) tuples.
        """
        storeSession = util.getStoreSession(ctx)
        return accessibleContentTypes(storeSession, self.application.contentTypes,'pagish')    

    
    def cbCreateItem(self, ctx, form, data):
        """
        Form callback to create an item.

        Once the item is created, the browser is redirected to the edit page.
        """

        # WHY DOES GETPLUGINNAME HAVE TO BE DEFERRED?
        def getPluginByName(pluginName):
            sess = util.getStoreSession(ctx)
            return defer.succeed(self.application.contentTypes.get(pluginName))
        
        def getSiteMapManager(avatar, sess):
            sm=self.application.sitemapManagerFactory(avatar,sess)
            return defer.succeed(sm)

        def getSiteMap(sma):
            return sma.loadSiteMap()
        
        def checkUrl(sm,path):
            item = sm.getNodeFromUrl(path)
            if item is not None:
                raise NodeAlreadyExists('This url already exists')
            return defer.succeed(True)
        
        def getUrlParent(sm, path):
            # TODO: Need to check for whether the path exists...
            if path=='/':
                return defer.succeed(None)
            parentUrl = '/'.join(path.split('/')[:-1])
            if parentUrl == '':
                parent = sm
            else:
                parent = sm.getNodeFromUrl(parentUrl)
            if parent is None:
                # TODO: Need to return a nice error saying - don't be silly!! should this be a value error? see previous call back too
                raise MissingParentNode('Cannot add page as it has no parent')
            else:
                return defer.succeed(parent)

        def createObject(contentPlugin, itemName):
            cm = self.application.getContentManager(self.avatar)
            return cm.createItem(sess, contentPlugin, itemName, avatar.user.name)


        # TODO: I've hardcoded cms here.. this seems wrong but I don'tknow where to get it from (tim)
        # TODO: I'm using split('/') and slices loads.. do we have a url util function? (tim)
        def addSiteMapNode(object, path, parent, siteMapManager,siteMap):
            if path=='/':
                if siteMap is not None:
                    return siteMapManager.updateNode(siteMap, 'cms', object.id, name='root',level=sitemapLevel,label=sitemapLabel)
                else:
                    return siteMapManager.insertRootNode('root',sitemapLabel,'cms', object.id, sitemapLevel)
            else:
                childName = path.split('/')[-1]
                # TODO: This will raise an error if the node isn't unique - we need to do this gracefully
                return siteMapManager.addChildToNode(parent, childName, sitemapLabel, 'cms', object.id, sitemapLevel)

        def objectCreated(obj):
            u = url.here.child(obj.id)
            return u.replace('message', 'Item added successfully')
        

        def errUnauthorized(failure):
            failure.trap(capabilities.UnauthorizedException)
            u = url.here
            return u.replace('errormessage', 'You do not have permission to create this item.')

        def errMissingParentNode(failure):
            failure.trap(MissingParentNode)
            u = url.here
            return u.replace('errormessage', 'A node has to be added below a node that already exists.')

        def errNodeAlreadyExists(failure):
            failure.trap(NodeAlreadyExists)
            u = url.here
            return u.replace('errormessage', 'This url already exists.')


        # Get the bits we need from the form data
        path = data['itemName']
        sitemapLabel = data['sitemapLabel']
        sitemapLevel = data['sitemapLevel']
        contentType = data['contentType']
        avatar = self.avatar
        sess = util.getStoreSession(ctx)
        
        # Add the item
        d = getPluginByName(contentType)
        d.addCallback(
            lambda plugin: getSiteMapManager(avatar,sess).addCallback(
                lambda siteMapManager: getSiteMap(siteMapManager).addCallback(
                    lambda siteMap: checkUrl(siteMap, path).addCallback(
                        lambda devnull: getUrlParent(siteMap, path).addCallback(
                            lambda parent: createObject(plugin, path).addCallback(
                                lambda object: addSiteMapNode(object, path, parent, siteMapManager, siteMap).addCallback(
                                    lambda resultOfInsert: objectCreated(object)
                )))))))
        d.addErrback(errUnauthorized)
        d.addErrback(errMissingParentNode)
        d.addErrback(errNodeAlreadyExists)
        return d
    
    


    

class FacetRenderer(object):
    implements(itabular.ICellRenderer)

    def __init__(self, categories=None, pattern=None):
        self.pattern = pattern or 'dataCell'
        self.categories = categories

    def rend(self, patterns, item, attribute):
        cell = patterns.patternGenerator(self.pattern)()

        categoryList = item.getAttributeValue('categories') or []
        values = []
        for category in categoryList:
            if not category:
                continue
            try:
                facet, category = category.split('.', 1)
            except ValueError:
                continue
            if facet == attribute:
                values.append(self._getNiceName(facet,category))
        cell.fillSlots('value', ','.join(values))
        return cell

    def _getNiceName(self, facet, category):
        # Need to find the label for the category
        return category

@defer.deferredGenerator
def accessibleContentTypes(storeSession, contentTypes, type):
    """
    Returns a list of the accessible (i.e. according to capabilities) content
    types.
    """
    # filter the content types by permission to create items of that type
    canCreate = []
    # TODO this really has to go!! How do I get a set of 'types' from the self.contentTypes list?
    nonpagishcontentypes=[ct for ct in contentTypes if 'Page' not in ct.name]
    pagishcontenttypes=[ct for ct in contentTypes if 'Page' in ct.name]
    if type == 'pagish':
        fullList = pagishcontenttypes
    else:
        fullList = nonpagishcontentypes
        
    for p in fullList:
        d = defer.maybeDeferred( storeSession.capCtx.getProxy, p )
        d = defer.waitForDeferred( d )
        yield d
        p = d.getResult()
        if p.testPermission( p.contentItemFactory ):
            canCreate.append( (p.description, p) )
    canCreate.sort()

    canCreate = [ (p[1].name, p[1].description) for p in canCreate]
    yield canCreate



class LanguageFormMixin(object):

    def render_languageform(self, ctx, data):
        if len(self.availableLanguages(ctx)) == 1:
            return ctx.tag.clear()

        tag = inevow.IQ(ctx.tag).onePattern('form')
        return tag


    def form_language(self, ctx):
        languages = self.availableLanguages(ctx)
        language = self.currentLanguage(ctx)
        form = xforms.Form()
        form.addField('language', xforms.String(),
                xforms.widgetFactory(LanguagesChoice, languages))
        form.addAction(self._switchLanguage, 'switch')
        form.addAction(self._deleteLanguage, 'delete')
        if language is not None:
            form.data = {'language': language}
        return form

    def _switchLanguage(self, ctx, form, data):
        """Language was switched.
        """
        if inevow.ICurrentSegments(ctx)[-1] == self.currentLanguage(ctx):
            urlFactory = url.URL.fromContext(ctx).sibling
        else:
            urlFactory = url.URL.fromContext(ctx).child
        return urlFactory(data['language'])

    def _deleteLanguage(self, ctx, form, data):
        pass


class LanguagesChoice(xforms.SelectChoice):
    """A drop down choice of the configured languages.
    """

    # Don't display the none option at all.
    noneOption = None

    def __init__(self, original, languages):
        super(LanguagesChoice, self).__init__(original)
        self.languages = languages

    def options(self, ctx, data):
        return [(l.code,l.name) for l in self.languages]


class EditContentPage(xforms.ResourceMixin, LanguageFormMixin, page.Page):
    """Edit a content object.
    """

    componentContent = loader('EditContentItem.html')

    WORKFLOW_STATUS_FIELD = 'workflowStatus'
    OLCOUNT_FIELD = 'olcount'
    VERSION_FIELD = 'version'
    CREATE_NEW_VERSION_ACTION = 'createNewVersion'
    UPDATE_ITEM_ATTRIBUTES_ACTION = 'updateItemAttributes'
    UPDATE_SYSTEM_ATTRIBUTES_ACTION = 'updateSystemAttributes'
    UPDATE_CATEGORIES_ACTION = 'updateCategories'
    UPDATE_EXTRA_DATA_ACTION = 'updateExtraData'

    workflowStates = [
            (contentitem.ContentItem.WORKFLOW_STATUS_EDITING, 'Editing'),
            (contentitem.ContentItem.WORKFLOW_STATUS_WAITING, 'Waiting Approval'),
            (contentitem.ContentItem.WORKFLOW_STATUS_APPROVED, 'Approved'),
            (contentitem.ContentItem.WORKFLOW_STATUS_REVOKED, 'Revoked')
        ]

    def __init__(self, application, avatar, original, language=None):
        xforms.ResourceMixin.__init__(self)
        LanguageFormMixin.__init__(self)
        page.Page.__init__(self)
        self.application = application
        self.avatar = avatar
        self.original = original
        self.language = language
        self.contentEditor = ContentEditor(self.application, self.original)

    def availableLanguages(self, ctx):
        return self.avatar.realm.languages

    def currentLanguage(self, ctx):
        """
        Return the current language that the page is editing or the default
        language is no specific language is in use.
        """
        if self.language is not None:
            return self.language
        return self.avatar.realm.defaultLanguage

    def isLatestVersion(self, ctx):
        """
        Return True if the resource is editing the latest version of the item
        it adapts.
        """
        def gotItem(item):
            return item.version == self.original.version
        sess = util.getStoreSession(ctx)
        d = sess.getItemById(self.original.id)
        d.addCallback(gotItem)
        return d

    def childFactory(self, ctx, name):
        if name in [l.code for l in self.avatar.realm.languages]:
            return self.__class__(self.application, self.avatar, self.original,
                    name)

    def _addHiddenFieldsToForm(self, form):
        form.addField(EditContentPage.OLCOUNT_FIELD, xforms.Integer(), xforms.Hidden)
        form.data[EditContentPage.OLCOUNT_FIELD]=self.original.olcount

        form.addField(EditContentPage.VERSION_FIELD, xforms.Integer(), xforms.Hidden)
        form.data[EditContentPage.VERSION_FIELD]=self.original.version

    def _copyHiddenFormFieldsFromData(self, data):
        self.original.olcount=data[EditContentPage.OLCOUNT_FIELD]
        self.original.version=data[EditContentPage.VERSION_FIELD]

    def _addSubmitButtonToForm(self, form, hasCapabilityToUpdate, default, text, ignoreChecks=False):
        approved = self._isItemApproved()
        if ignoreChecks or (not approved and hasCapabilityToUpdate):
            form.addAction(default, text)

    def _isItemApproved(self):
        return self.original.workflowStatus in [
                contentitem.ContentItem.WORKFLOW_STATUS_APPROVED,
                contentitem.ContentItem.WORKFLOW_STATUS_REVOKED]

    def _isReadOnly(self, hasCapabilityToUpdate):
        if self._isItemApproved():
            return True
        if not hasCapabilityToUpdate:
            return True
        return False

    def render_editForms(self, ctx, data):
        return ctx.tag

    @defer.deferredGenerator
    def form_editItem(self, ctx):

        hasCapabilityToUpdate = self.original.testPermission(self.original.setAttributeValues)
        immutable = self._isReadOnly(hasCapabilityToUpdate)

        # Check for latest version
        d = defer.waitForDeferred(self.isLatestVersion(ctx))
        yield d
        isLatestVersion = d.getResult()

        # Get the form
        d = defer.waitForDeferred(defer.maybeDeferred(self.contentEditor.getForm,
            ctx, self.currentLanguage(ctx), immutable))
        yield d
        form = d.getResult()

        # Complete the form
        self._addHiddenFieldsToForm(form)
        if isLatestVersion:
            self._addSubmitButtonToForm(form, hasCapabilityToUpdate,
                self._submit, EditContentPage.UPDATE_ITEM_ATTRIBUTES_ACTION)
            self._addSubmitButtonToForm(form, hasCapabilityToUpdate,
                self._submitAndApprove, 'Submit and Approve')
        yield form

    def _submit(self, ctx, form, data):
        # TODO: This needs to check that the name hasn't changed... if it has then we need to update the sitemap (if we can)
        d = defer.maybeDeferred(self.contentEditor.save, ctx, form, data, self.currentLanguage(ctx))
        d.addCallback(lambda spam: self._handleSubmit(ctx, form, data))
        self._addErrbacks(ctx, d)
        return d




    def _submitAndApprove(self,ctx,form,data):
        def approve(spam):
            d = self.original.setWorkflowApproved()
            d.addCallback(lambda ignore: self.application.contentIndex.checkedIndexItem(self.original))
            return d


        d = defer.maybeDeferred(self.contentEditor.save, ctx, form, data, self.currentLanguage(ctx))
        
        sess = util.getStoreSession(ctx)
        hasCapabilityToUpdate = self.original.testPermission(self.original.setSystemAttributeValues)
        immutable = self._isReadOnly(hasCapabilityToUpdate)
        ## Check the item is now complete
        if not self.original.isComplete():
            return url.URL.fromContext(ctx).replace('errormessage', MSG_NOT_COMPLETE)
        d.addCallback(approve)
        d.addCallback(lambda spam: self._handleSubmit(ctx, form, data))
        #self._addErrbacks(ctx, d)
        #d.callback(None)
        return d    
       

    @defer.deferredGenerator
    def form_editCategories(self, ctx):

        def addAttributesToForm(form, attributes, immutable):
            for attr in attributes:
                attr.type.immutable = immutable
                form.addField(attr.name, attr.type, widgetFactory=attr.widgetFactory)

        sess = util.getStoreSession(ctx)
        hasCapabilityToUpdate = self.original.testPermission(self.original.setCategoriesAttributeValues)

        # Check for latest version
        d = defer.waitForDeferred(self.isLatestVersion(ctx))
        yield d
        isLatestVersion = d.getResult()

        # Find the plugin
        d = defer.waitForDeferred(defer.maybeDeferred(
                self.application.contentTypes.getTypeForItem, self.original))
        yield d
        plugin = d.getResult()

        # Create the form
        form = xforms.Form()
        immutable = self._isReadOnly(hasCapabilityToUpdate)
        addAttributesToForm(form, plugin.contentItemClass.getCategoriesAttributes(), immutable)
        form.data = self.original.getCategoriesAttributeValues(self.currentLanguage(ctx))
        self._addHiddenFieldsToForm(form)
        if isLatestVersion:
            self._addSubmitButtonToForm(form, hasCapabilityToUpdate,
                self._submitCategoriesAttributes, EditContentPage.UPDATE_CATEGORIES_ACTION)

        yield form

    def _submitCategoriesAttributes(self, ctx, form, data):
        sess = util.getStoreSession(ctx)
        d = defer.maybeDeferred(self.original.setCategoriesAttributeValues, sess, self.currentLanguage(ctx), **data)
        d.addCallback(lambda spam: self._handleSubmit(ctx, form, data))
        self._addErrbacks(ctx, d)
        return d

    def _addWorkflowFieldToForm(self, form):
        type = xforms.Integer(required=True)

        # Read only view of the workflow
        type.immutable = True
        states = EditContentPage.workflowStates

        if self.original.workflowStatus == contentitem.ContentItem.WORKFLOW_STATUS_APPROVED:
            # If item is approved, it can only be revoked
            if self.original.testPermission(self.original.setWorkflowRevoked):
                states = EditContentPage.workflowStates[2:4]
                type.immutable = False
        elif self.original.workflowStatus != contentitem.ContentItem.WORKFLOW_STATUS_REVOKED:
            # Item has not been revoked
            if self.original.testPermission(self.original.setWorkflowApproved):
                # Item can be approved
                states = EditContentPage.workflowStates[0:3]
                type.immutable = False
            elif self.original.testPermission(self.original.setAttributeValues):
                # Item cannot be approved
                states = EditContentPage.workflowStates[0:2]
                type.immutable = False

        form.addField(EditContentPage.WORKFLOW_STATUS_FIELD, type,
            widgetFactory=xforms.widgetFactory(xforms.SelectChoice, states, noneOption=None) )

        form.data[EditContentPage.WORKFLOW_STATUS_FIELD] = self.original.workflowStatus
        return not type.immutable

    def _addTemplateFieldToForm(self, form, plugin, immutable):
        type = xforms.String(required=True, immutable=immutable)
        states = [(t[0],t[1]) for t in plugin.templates]
        form.addField('template', type,
            widgetFactory=xforms.widgetFactory(xforms.SelectChoice, states, noneOption=None) )


        form.data['template'] = getattr(self.original,'template',None)


    @defer.deferredGenerator
    def form_editSystemAttributes(self, ctx):

        def addAttributesToForm(form, attributes, immutable):
            for attr in attributes:
                attr.type.immutable = immutable
                form.addField(attr.name, attr.type, widgetFactory=attr.widgetFactory)

        sess = util.getStoreSession(ctx)
        hasCapabilityToUpdate = self.original.testPermission(self.original.setSystemAttributeValues)

        # Check for latest version
        d = defer.waitForDeferred(self.isLatestVersion(ctx))
        yield d
        isLatestVersion = d.getResult()

        # Get the plugin
        d = defer.waitForDeferred(defer.maybeDeferred(
                self.application.contentTypes.getTypeForItem, self.original))
        yield d
        plugin = d.getResult()

        form = xforms.Form()
        immutable = self._isReadOnly(hasCapabilityToUpdate)
        addAttributesToForm(form, plugin.contentItemClass.getSystemAttributes(), immutable)
        form.data = self.original.getSystemAttributeValues(self.currentLanguage(ctx))
        if plugin.templates is not None:
            self._addTemplateFieldToForm(form,plugin,immutable)
        workflowUpdateable = self._addWorkflowFieldToForm(form)
        self._addHiddenFieldsToForm(form)
        if workflowUpdateable:
            self._addSubmitButtonToForm(form, hasCapabilityToUpdate or workflowUpdateable,
                self._submitSystemAttributes, EditContentPage.UPDATE_SYSTEM_ATTRIBUTES_ACTION,
                True)
        yield form

    def _submitSystemAttributes(self, ctx, form, data):

        def setWorkflowStatus(spam):
            workflowStatus = data.get(EditContentPage.WORKFLOW_STATUS_FIELD, None)
            if workflowStatus is None or workflowStatus == self.original.workflowStatus:
                return

            if workflowStatus == contentitem.ContentItem.WORKFLOW_STATUS_EDITING:
                return self.original.setWorkflowEditing()
            elif workflowStatus == contentitem.ContentItem.WORKFLOW_STATUS_WAITING:
                return self.original.setWorkflowWaiting()
            elif workflowStatus == contentitem.ContentItem.WORKFLOW_STATUS_APPROVED:
                d = self.original.setWorkflowApproved()
                d.addCallback(lambda ignore: self.application.contentIndex.checkedIndexItem(self.original))
                return d
            elif workflowStatus == contentitem.ContentItem.WORKFLOW_STATUS_REVOKED:
                d = self.original.setWorkflowRevoked()
                d.addCallback(lambda ignore: self.application.contentIndex.removeItem(self.original.id))
                return d

        sess = util.getStoreSession(ctx)
        hasCapabilityToUpdate = self.original.testPermission(self.original.setSystemAttributeValues)
        immutable = self._isReadOnly(hasCapabilityToUpdate)

        d = defer.Deferred()
        if not immutable:
            d.addCallback(lambda ignore: self.original.setSystemAttributeValues(sess, self.currentLanguage(ctx), **data))
            
            if 'template' in data:
                self.original.template = data['template']
                
            

        # Check the item is now complete
        if data.get(EditContentPage.WORKFLOW_STATUS_FIELD, None) == contentitem.ContentItem.WORKFLOW_STATUS_APPROVED \
            and not self.original.isComplete():
            return url.URL.fromContext(ctx).replace('errormessage', MSG_NOT_COMPLETE)
        d.addCallback(setWorkflowStatus)
        d.addCallback(lambda spam: self._handleSubmit(ctx, form, data))
        self._addErrbacks(ctx, d)
        d.callback(None)
        return d

    def render_immutable(self,ctx,data):
        hasCapabilityToUpdate = self.original.testPermission(self.original.setSystemAttributeValues)
        immutable = self._isReadOnly(hasCapabilityToUpdate)
        if immutable == True:
            return 'immutable'
        return 'editable'

    def _handleSubmit(self, ctx, form, data):
        sess = util.getStoreSession(ctx)

        def objectUpdated(spam):
            return url.URL.fromContext(ctx).replace('message',
                'Item update successfully')

        self._copyHiddenFormFieldsFromData(data)
        d = sess.flush()
        d.addCallback(objectUpdated)
        return d

    def _addErrbacks(self, ctx, d):
        sess = util.getStoreSession(ctx)

        def catchNotFoundException(failure):
            failure.trap(NotFound)
            sess.forceRollback = True
            return url.URL.fromContext(ctx).replace('errormessage',
                'Item update failed. Someone else has already changed the item.')

        def catchUnauthorizedException(failure):
            failure.trap(capabilities.UnauthorizedException)
            sess.forceRollback = True
            return url.URL.fromContext(ctx).replace('errormessage',
                'You do not have permission to update this item.')

        d.addErrback(catchNotFoundException)
        d.addErrback(catchUnauthorizedException)
        return d

    def locateChild(self, ctx, segments):

        def catchNoFormException(failure):
            if failure.getErrorMessage() == 'The form has no callback and no action was found.':
                u = url.URL.fromContext(ctx).replace('errormessage',
                    'Item update failed. Someone else has already changed the item.')
                return u, []
            return failure

        d = defer.maybeDeferred( super(EditContentPage, self).locateChild, ctx, segments)
        d.addErrback(catchNoFormException)
        return d

    def render_versionInfo(self, ctx, data):
        """
        Render the version state and related actions.

        The renderer uses patterns to fill in the following:
              * current state
              * link to previous/lates version
              * create new version action
        """

        def versionLink(version=None):
            # Get a url to the beginning
            segments = inevow.ICurrentSegments(ctx)
            link = url.URL.fromContext(ctx).up()
            # Adjust for the language
            if not segments[-1].startswith(str(self.original.id)):
                language = segments[-1]
                link = link.up()
            else:
                language = None
            if version is None:
                link=link.child(self.original.id)
            else:
                link=link.child('%dv%d'%(self.original.id, version))
            if language is not None:
                link=link.child(language)
            return link

        def chooseView(isLatestVersion):

            approved = self._isItemApproved()
            hasCapabilityToUpdate = self.original.testPermission(self.original.setAttributeValues)
            version = self.original.version

            if isLatestVersion:
                if version == 1:
                    versionTag = ctx.tag.onePattern('label-only')
                    linkTag = ''
                else:
                    versionTag = ctx.tag.onePattern('label-latest')
                    linkTag = ctx.tag.onePattern('link-previous')
                    linkTag.fillSlots('link', versionLink(version-1))
            else:
                versionTag = ctx.tag.onePattern('label-previous')
                linkTag = ctx.tag.onePattern('link-latest')
                linkTag.fillSlots('link', versionLink())

            if approved and isLatestVersion and hasCapabilityToUpdate:
                actionTag = ctx.tag.onePattern('action-create')
                actionTag.fillSlots('action', url.here.child('_createNewVersion'))
                actionTag.fillSlots('olcount', self.original.olcount)
                actionTag.fillSlots('version', self.original.version)
            else:
                actionTag = ''

            # Emit the tag
            return ctx.tag.clear()[versionTag, linkTag, actionTag]

        d = self.isLatestVersion(ctx)
        d.addCallback(chooseView)
        return d

    def child__createNewVersion(self, ctx):

        sess = util.getStoreSession(ctx)
        avatar = self.avatar

        # We use these to make sure the user who clicked the button was looking
        # at the latest version. We cannot use self.original for this because it
        # will have been reloaded as the resource was created.
        olcount = int(ctx.arg(EditContentPage.OLCOUNT_FIELD))
        version = int(ctx.arg(EditContentPage.VERSION_FIELD))

        # Actually, we're going to abuse things horribly ... sorry!
        self.original.version = version
        self.original.olcount = olcount

        def newVersionCreated(obj):
            u = url.URL.fromContext(ctx)
            return u.replace('message', 'New version created successfully')

        def updateFailed(failure):
            failure.trap(NotFound)
            sess.forceRollback = True
            return url.URL.fromContext(ctx).replace('errormessage', 'Item update failed. Someone else has already changed the item.')

        def catchUnauthorizedException(failure):
            failure.trap(capabilities.UnauthorizedException)
            sess.forceRollback = True
            u = url.URL.fromContext(ctx)
            return u.replace('errormessage', 'You do not have permission to create a new version of this item.')

        d = self.application.getContentManager(avatar).createNewVersion(sess, self.original)
        d.addCallback(lambda r: sess.flush())
        d.addCallback(newVersionCreated)
        d.addErrback(catchUnauthorizedException)
        return d

    def render_languagecss(self, ctx, data):
        return self.renderLanguageCSSHelper(ctx, data, self.currentLanguage(ctx))

    def render_tinyMCEinit(self, ctx, data):
        return self.renderTinyMCEInitHelper(ctx, data, self.currentLanguage(ctx))

    @defer.deferredGenerator
    def form_editExtraData(self, ctx):

        def addAttributesToForm(form, attributes, immutable):
            for attr in attributes:
                attr.type.immutable = immutable
                form.addField(attr.name, attr.type, widgetFactory=attr.widgetFactory)

        sess = util.getStoreSession(ctx)
        hasCapabilityToUpdate = self.original.testPermission(self.original.setExtraDataAttributeValues)

        # Check for latest version
        d = defer.waitForDeferred(self.isLatestVersion(ctx))
        yield d
        isLatestVersion = d.getResult()

        # Find the plugin
        d = defer.waitForDeferred(defer.maybeDeferred(
                self.application.contentTypes.getTypeForItem, self.original))
        yield d
        plugin = d.getResult()

        # Create the form
        form = xforms.Form()
        immutable = self._isReadOnly(hasCapabilityToUpdate)
        addAttributesToForm(form, plugin.contentItemClass.getExtraDataAttributes(), immutable)
        form.data = self.original.getExtraDataAttributeValues(self.currentLanguage(ctx))
        self._addHiddenFieldsToForm(form)
        if isLatestVersion:
            self._addSubmitButtonToForm(form, hasCapabilityToUpdate,
                self._submitExtraDataAttributes, EditContentPage.UPDATE_EXTRA_DATA_ACTION)

        yield form

    def _submitExtraDataAttributes(self, ctx, form, data):
        sess = util.getStoreSession(ctx)
        d = defer.maybeDeferred(self.original.setExtraDataAttributeValues, sess, self.currentLanguage(ctx), **data)
        d.addCallback(lambda spam: self._handleSubmit(ctx, form, data))
        self._addErrbacks(ctx, d)
        return d


class EditFragmentPage(EditContentPage):    

    @defer.inlineCallbacks
    def form_editItem(self, ctx):
        ## WE NEED TO TRANSFORM THE DATA FROM THE DATA FIELD INTO THE DATA FOR THE FRAGMENTTYPE FORM DEFINITION.
        ## SO FIRST WE NEED TO GET THE FRAGMENT TYPE OUT..

        hasCapabilityToUpdate = self.original.testPermission(self.original.setAttributeValues)
        immutable = self._isReadOnly(hasCapabilityToUpdate)

        # Check for latest version
        isLatestVersion = yield self.isLatestVersion(ctx)

        # Get the form
        form = xforms.Form()
        form.addField('name', xforms.String(required=True, immutable=immutable))
        # This is where we need to build the form from the formData and also to get the attribute values from self.original based on this form data
        sess = util.getStoreSession(ctx)
        items = yield sess.getItems(fragmenttype.FragmentType)
        for item in items:
            if item.name == self.original.protectedObject.type:
                fragmentType = item
                break
            
        formDefinitionString = fragmentType.formDefinition
        import syck
        from StringIO import StringIO
        f = StringIO(formDefinitionString.encode('ascii'))
        formDefinition = syck.load(f)   
        from formalbuilder import builder
        if immutable:
            for item in formDefinition:
                item['immutable'] = True
        builder.addFormItems(form,formDefinition)

        if hasattr(self.original,'data'):
            form.data = self.original.data
        form.data['name'] = self.original.name
        form.data['template'] = fragmentType.template


        # Complete the form
        self._addHiddenFieldsToForm(form)
        if isLatestVersion:
            self._addSubmitButtonToForm(form, hasCapabilityToUpdate,
                self._submit, EditContentPage.UPDATE_ITEM_ATTRIBUTES_ACTION)
            self._addSubmitButtonToForm(form, hasCapabilityToUpdate,
                self._submitAndApprove, 'Submit and Approve')
        returnValue(form)

    def _submit(self, ctx, form, data):
        ## WE NEED TO TRANSFORM THE DATA FROM THE FRAGMENTTYPE FIELDS TO THE SIMPLE DATA FIELD.
        # TODO: This needs to check that the name hasn't changed... if it has then we need to update the sitemap (if we can)
        self.original.data = data
        self.original.name = data['name']
        self.original.touch()
        d = self._handleSubmit(ctx, form, data)
        return d

    def _submitAndApprove(self,ctx,form,data):
        def approve():
            d = self.original.setWorkflowApproved()
            d.addCallback(lambda ignore: self.application.contentIndex.checkedIndexItem(self.original))
            return d

        self.original.data = data
        self.original.name = data['name']
        self.original.touch()
        d = approve()
        d.addCallback(lambda spam: self._handleSubmit(ctx, form, data))
        return d     

class EditableResourceFactory(object):

    def __init__(self, contentItem):
        self.contentItem = contentItem

    def createEditableResource(self, application, avatar):
        if type(self.contentItem.getProtectedObject()) == fragment.Fragment:
            return EditFragmentPage(application, avatar, self.contentItem)
        return EditContentPage(application, avatar, self.contentItem)


registerAdapter(EditableResourceFactory, contentitem.ContentItem,
        icms.IEditableResourceFactory)


class ContentEditor(object):
    implements(icms.IContentEditor)

    def __init__(self, application, obj):
        self.application = application
        self.obj = obj
        self.pluginContentEditor = icms.IContentEditor(obj)

    def getForm(self, ctx, language, immutable):
        sess = util.getStoreSession(ctx)
        d = defer.maybeDeferred(self.application.contentTypes.getTypeForItem,
                self.obj)

        def callPluginContentEditor(plugin):
            return self.pluginContentEditor.getForm(ctx, language, plugin, immutable)
        d.addCallback(callPluginContentEditor)
        return d

    def save(self, ctx, form, data, language):
        return self.pluginContentEditor.saveAttributes(ctx, form, data, language)



def decodeIdVersion(name):
    # id may be encoded with a version e.g. id;version
    name = name.split('v')
    id = None
    version = None
    if len(name) > 1:
        version = int(name[1])
    id = int(name[0])
    return id,version


def encodeIdVersion(id, version, includeVersion=True):
    if includeVersion:
        return '%dv%d'%(int(id),int(version))
    else:
        return '%d'%(int(id),)

