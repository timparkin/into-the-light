#from zope.interface import Interface, implements
#from twisted.cred import portal
#from twisted.internet import defer
#from twisted.python import components
#from nevow import tags as T, url
#import forms
#from cms import store, icms
#from cms.web.cmsforms import segment, treewidget
#from cms.web.admin import util

import re 
from zope.interface import implements, Interface
from twisted.python import components
from nevow import tags as T, url
from nevow.i18n import _

from tub import capabilities, error
from tub.web import page, util as tub_util, xforms
from sitemap import segment, treewidget, manager
from tub.capabilities import UnauthorizedException




class ICurrentNodeInfo(Interface):
    pass


class ISiteMapItemTreeNode(treewidget.ITreeNode):
    """Subclass of ITreeNode specifically for manager.SiteMapItems. This
    allows us to special-case the adaption.
    """

class SiteMapItemTreeNodeAdapter(object):
    """Adapt a SiteMapItem instance to the ISiteMapItemTreeNode interface.
    """
    implements(ISiteMapItemTreeNode)

    def __init__(self, original):
        self.original = original

    def label():
        """Build the label property.
        """
        def get(self):
            def renderer(ctx, data):
                rootNode, u = ctx.locate(ICurrentNodeInfo)
                path = self.original.path.split('.')[1:]
                for segment in path:
                    u = u.child(segment)
                return T.a(href=u)[self.original.name]
            return renderer
        return property(get)

    value = property(lambda self: self.original.id)
    label = label()
    children = property(lambda self: self.original.children)

components.registerAdapter(SiteMapItemTreeNodeAdapter, manager.SiteMapItem, ISiteMapItemTreeNode)


class ICurrentSiteMapNode(Interface):
    """Marker interface for remembering the current site map node that is
    being edited.
    """
    
def loader(filename):
    """
    Load a template from this package's templates directory.
    """
    return tub_util.PackageTemplate('sitemap.templates',
            filename, ignoreDocType=True)

def debug(r, msg):
    print '>>DEBUG', msg, r
    return r


class SiteMapPage(xforms.ResourceMixin, page.Page):
    """The site map management page
    """
    componentContent = loader('SiteMap.html')
    rootPath = 'root'

    def __init__(self, *a, **kw):
        manager = kw.pop('manager')
        page.Page.__init__(self, *a, **kw)
        self.remember(self.original, ICurrentSiteMapNode)
        self.manager = manager

    def _rememberCurrentNodeInfo(self, ctx):
        # TODO: Do I need to do this?

        try:
            ctx.locate( ICurrentNodeInfo )
        except KeyError:
            ctx.remember( (self.original, url.URL.fromContext(ctx)), ICurrentNodeInfo )

    def childFactory(self, ctx, name):
        """Find a child node with the segment name.
        """
        self._rememberCurrentNodeInfo(ctx)
        for node in self.original.children:
            if node.name == name:
                return self.__class__(node, manager=self.manager)

    def beforeRender(self, ctx):
        self._rememberCurrentNodeInfo(ctx)

    def render_breadcrumb(self,ctx,data):
        rootnode, u = ICurrentNodeInfo(ctx)
#        u = u.child('nav')

        ctx.tag.clear()
        breadcrumb = ctx.tag
        breadcrumb[ T.invisible()[ ('http:// ',T.a(href=u)[url.URL.fromContext(ctx).netloc],T.xml('&nbsp;/&nbsp;')) ] ]
        top = rootnode
        for segment in self.original.path.split('.')[1:]:
            if segment != top.name:
                for node in top.children:
                    if node.name == segment:
                        label = node.name
                        top = node
                        break
            else:
                label = top.name
            u = u.child(segment)
            if segment != self.original.name:
                breadcrumb[ ( ( T.a(href=u)[label], T.xml('&nbsp;/&nbsp;') ) ) ]
            else:
                breadcrumb[ label ]
        return breadcrumb


    def _mapItemName(self, itemName):
        """Map an item name into something that can be used in a select choice"""
        return '%s_%s'%(itemName[0], itemName[1])

    def _mapItem(self, item):
        """Map a SiteMapItem into something that can be used in a select choice"""
        return '%s_%s'%(item.app, item.itemId)

    def _unmapItem(self, data):
        r = re.match('^(?P<app>.+)_(?P<id>\d+)$', data)
        if not r:
            raise "Invalid data"
        return r.group('app'), r.group('id')
        

    def data_items(self, ctx, cata):
        """Retrieve a list of the names of all items that can appear in the site map.
        """
        def gotItems(items):
            for item in items:
                yield self._mapItemName(item), item[2]

        d = self.manager.getNamesOfItems()
        d.addCallback(gotItems)
        return d


    def form_editPage(self, ctx):
        """Create a form for editing this node's general information.
        """
        form = xforms.Form()
        if self.original.path != self.rootPath:
            form.addField('nodeName', segment.Segment(required=True, message='Invalid segment name'), xforms.TextInput)
        form.addField('page', xforms.String(required=True), lambda original: xforms.SelectChoice(original, self.data_items))
        form.addField('navigationLabel', xforms.String(required=True), xforms.TextInput)
        if self.original.path != self.rootPath:
            navigationLevels = self.manager.navigationLevels
            form.addField('navigationLevel', xforms.Integer(), lambda original: xforms.SelectChoice(original, navigationLevels))
        form.addAction(self._submit_editPage,'change')
        form.data = {
            'page': self._mapItem(self.original),
            'nodeName': self.original.name,
            'navigationLabel': self.original.label,
            'navigationLevel': self.original.level,
            }
        return form

    def _submit_editPage(self, ctx, form, data):
        """Handle editPage form submission.
        """

        storeSession = tub_util.getStoreSession(ctx)
        def nodeUpdated(r):
            if self.original.path == self.rootPath:
                u = url.URL.fromContext(ctx)
            else:
                u = url.URL.fromContext(ctx).sibling(self.original.name)
            return u.replace('message', 'Site Map node updated successfully')

        def catchUnauthorizedException(failure):
            failure.trap(UnauthorizedException)
            u = url.URL.fromContext(ctx)
            storeSession.forceRollback = True
            return u.replace('errormessage', 'You do not have permission to update the site map.')

        app, id = self._unmapItem(data['page'])
        if self.original.path != self.rootPath:
            d = self.manager.updateNode(self.original, app, id, name=data['nodeName'], label=data['navigationLabel'], level=data['navigationLevel'])
        else:
            d = self.manager.updateNode(self.original, app, id, label=data['navigationLabel'])
        d.addCallback(nodeUpdated)
        d.addErrback(catchUnauthorizedException)
        return d

    def form_editChildren(self,ctx):
        """Create a form for managing the children (a tree) of this node.
        """
        children = self.original.children
        form = xforms.Form()
        if children:
            form.addField(
                'navigation',
                xforms.Integer(required=True),
                xforms.widgetFactory(treewidget.RadioTreeChoice, children, 
                    nodeInterface=ISiteMapItemTreeNode)
                )
            form.addAction(self._submit_deleteNode,'delete')
            form.addAction(self._submit_moveUp,'moveUp')
            form.addAction(self._submit_moveDown,'moveDown')
        return form

    def _submit_deleteNode(self, ctx, form, data):
        storeSession = tub_util.getStoreSession(ctx)
        def nodeRemoved(r):
            return url.URL.fromContext(ctx).replace('message', 'Child site map node deleted successfully')
        def catchUnauthorizedException(failure):
            failure.trap(UnauthorizedException)
            u = url.URL.fromContext(ctx)
            storeSession.forceRollback = True
            return u.replace('errormessage', 'You do not have permission to update the site map.')
        d = self.manager.removeNode(self.original.findChildById(data['navigation']))
        d.addCallback(nodeRemoved)
        d.addErrback(catchUnauthorizedException)
        return d

    def _submit_moveUp(self, ctx, form, data):
        return self._moveNode(ctx, data['navigation'], 'up')

    def _submit_moveDown(self, ctx, form, data):
        return self._moveNode(ctx, data['navigation'], 'down')

    def _moveNode(self, ctx, nodeId, direction):
        storeSession = tub_util.getStoreSession(ctx)
        def nodeMoved(r):
            return url.URL.fromContext(ctx).replace('message', 'Child site map node moved successfully')
        def catchUnauthorizedException(failure):
            failure.trap(UnauthorizedException)
            u = url.URL.fromContext(ctx)
            storeSession.forceRollback = True
            return u.replace('errormessage', 'You do not have permission to update the site map.')
        d = self.manager.moveNode(self.original.findChildById(nodeId), direction)
        d.addCallback(nodeMoved)
        d.addErrback(catchUnauthorizedException)
        return d

    def form_addNode(self, ctx):
        """Create a form for adding a new subpage to this node.
        """
        form = xforms.Form()
        form.addField('page', xforms.String(required=True), lambda original: xforms.SelectChoice(original, self.data_items))
        form.addField('nodeName', segment.Segment(required=True, message='Invalid segment name'), xforms.TextInput)
        navigationLevels = self.manager.navigationLevels
        form.addField('navigationLabel', xforms.String(required=True), xforms.TextInput)
        form.addField('navigationLevel', xforms.Integer(),  lambda original: xforms.SelectChoice(original, navigationLevels))
        form.addAction(self._submit_addNode,'add')
        return form

    def _submit_addNode(self, ctx, form, data):
        storeSession = tub_util.getStoreSession(ctx)
        def nodeAdded(r):
            return url.URL.fromContext(ctx).replace('message', 'Child site map node added successfully')
        def nodeAddError( failure ):
            failure.trap(error.NotUniqueError) 
            storeSession.forceRollback = True
            raise xforms.FieldValidationError( 'duplicate node', 'nodeName' )
        def catchUnauthorizedException(failure):
            failure.trap(UnauthorizedException)
            u = url.URL.fromContext(ctx)
            storeSession.forceRollback = True
            return u.replace('errormessage', 'You do not have permission to update site map.')

        self._checkReservedNodes( ctx, data['nodeName'] )

        app, id = self._unmapItem(data['page'])
        d = self.manager.addChildToNode(self.original, data['nodeName'], data['navigationLabel'], app, id, data['navigationLevel'])
        d.addErrback(catchUnauthorizedException)
        d.addCallbacks(nodeAdded,nodeAddError)
        return d

    def _checkReservedNodes( self, ctx, newChild ):
        reservedNodes = self.manager.reservedNodes
        if reservedNodes is None:
            return
        if self.original.path.find( '.' ) != -1:
            return
        if newChild in reservedNodes:
            raise xforms.FieldValidationError( 'reserved node', 'nodeName' )
