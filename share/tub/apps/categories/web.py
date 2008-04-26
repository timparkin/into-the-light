from zope.interface import implements
from twisted.python import components
from nevow import loaders, tags as T, url

from tub import capabilities, category, error
from tub.web import page, util, xforms


def loader(filename):
    """
    Load a template from this package's templates directory.
    """
    return util.PackageTemplate('tub.apps.categories.templates',
            filename, ignoreDocType=True)


class IEditableTreeNode(xforms.ITreeNode):
    """
    Specialised ITreeNode interface to allow adaption of Category objects for
    editing.
    """


class FacetsPage(page.Page):
    """
    List facets
    """

    componentContent = loader('FacetsPage.html')

    def __init__(self, avatar):
        super(FacetsPage, self).__init__(self)
        self.avatar = avatar

    def data_facets(self,ctx,data):
        # Get a list of category facets
        def getFacetNames(facets):
            facets = [ {'label':f[2],'textid':f[1]} for f in facets ]
            return facets
        storeSession = util.getStoreSession(ctx)
        d = self.avatar.getCategoryManager(storeSession)
        d.addCallback(lambda categories: categories.loadFacets())
        d.addCallback(getFacetNames)
        return d

    def render_facet(self,ctx,data):
        ctx.fillSlots('href',url.here.child(data['textid']))
        ctx.fillSlots('label',data['label'])
        return ctx.tag

    def childFactory(self, ctx, name):
        storeSession = util.getStoreSession(ctx)
        d = self.avatar.getCategoryManager(storeSession)
        d.addCallback(lambda categories: categories.loadCategories(name))
        d.addCallback(lambda facet: FacetNodePage(self.avatar, facet))
        return d


class FacetNodePage(xforms.ResourceMixin, page.Page):
    """
    Edit a facet's category node.
    """

    componentContent = loader('FacetPage.html')

    def __init__(self, avatar, facet, node=None):
        super(FacetNodePage, self).__init__()
        self.avatar = avatar
        self.facet = facet
        if node is None:
            node = self.facet
        self.node = node

    def childFactory(self, ctx, name):
        """Find a child node with the segment name.
        """
        for node in self.node.children:
            if node.textid == name:
                return self.__class__(self.avatar, self.facet, node)

    def render_breadcrumb(self,ctx,data):
        nodes = [self.facet]
        for segment in self.node.path.split('.')[1:]:
            node = nodes[-1].findChildBySegment(segment)
            nodes.append(node)
        nodes.reverse()
        u = None
        tags = []
        for node in nodes:
            if u is None:
                u = url.here
            else:
                u = u.up()
            tags.append(T.xml('&nbsp;&gt;&nbsp;'))
            tags.append(T.a(href=u)[node.label])
        tags.reverse()
        tags = tags[:-1]
        return ctx.tag.clear()[tags]

    # EDIT CATEGORY

    def form_editCategory(self, ctx):
        """Create a form for editing this node's general information.
        """
        form = xforms.Form()
        if self.facet.textid != self.node.textid:
            form.addField('textid', xforms.URLSegment(required=True))
            form.addField('label', xforms.String(required=True))
            form.addAction(self._submit_editCategory,'change')
            form.data = {
            'textid': self.node.textid,
            'label': self.node.label,
            }
        return form

    def _submit_editCategory(self, ctx, form, data):
        """Handle editCategory form submission.
        """

        def categoryUpdated(r):
            u = url.URL.fromContext(ctx).sibling(self.node.textid)
            return u.replace('message', 'Category updated succesfully')

        def catchUnauthorizedException(failure):
            failure.trap(capabilities.UnauthorizedException)
            u = url.URL.fromContext(ctx)
            sess.forceRollback = True
            return u.replace('errormessage', 'You do not have permission to update categories.')

        storeSession = util.getStoreSession(ctx)
        d = self.avatar.getCategoryManager(storeSession)
        d.addCallback(lambda categories: categories.updateNode(self.node, data['textid'], data['label']))
        d.addCallback(categoryUpdated)
        d.addErrback(catchUnauthorizedException)
        return d

    # EDIT CHILDREN

    def form_editChildren(self,ctx):
        """Create a form for managing the children (a tree) of this category.
        """
        children = self.node.children
        form = xforms.Form()
        if children:
            form.addField(
                'categories',
                xforms.Integer(required=True),
                xforms.widgetFactory(xforms.RadioTreeChoice, children,
                    nodeInterface=IEditableTreeNode)
                )
            form.addAction(self._submit_deleteCategory,'delete')
            form.addAction(self._submit_moveUp,'moveUp')
            form.addAction(self._submit_moveDown,'moveDown')
        return form

    def _submit_deleteCategory(self, ctx, form, data):
        def deleted(r):
            return url.URL.fromContext(ctx).replace('message', 'Category deleted successfully')

        def catchUnauthorizedException(failure):
            failure.trap(capabilities.UnauthorizedException)
            u = url.URL.fromContext(ctx)
            sess.forceRollback = True
            return u.replace('errormessage', 'You do not have permission to update categories.')

        storeSession = util.getStoreSession(ctx)
        d = self.avatar.getCategoryManager(storeSession)
        d.addCallback(lambda categories: categories.removeNode(self.node.findChildById(data['categories'])))
        d.addCallback(deleted)
        d.addErrback(catchUnauthorizedException)
        return d

    def _submit_moveUp(self, ctx, form, data):
        return self._moveCategory(ctx, data['categories'], 'up')

    def _submit_moveDown(self, ctx, form, data):
        return self._moveCategory(ctx, data['categories'], 'down')

    def _moveCategory(self, ctx, textid, direction):
        def moved(r):
            return url.URL.fromContext(ctx).replace('message', 'Category moved successfully')

        def catchUnauthorizedException(failure):
            failure.trap(capabilities.UnauthorizedException)
            u = url.URL.fromContext(ctx)
            sess.forceRollback = True
            return u.replace('errormessage', 'You do not have permission to update categories.')

        storeSession = util.getStoreSession(ctx)
        d = self.avatar.getCategoryManager(storeSession)
        d.addCallback(lambda categories: categories.moveNode(self.node.findChildById(textid), direction))
        d.addCallback(moved)
        d.addErrback(catchUnauthorizedException)
        return d

    # ADD CATEGORY FORM

    def form_addCategory(self, ctx):
        """Create a form for adding a new sub-category to this category
        """
        form = xforms.Form()
        form.addField('textid', xforms.URLSegment(required=True))
        form.addField('label', xforms.String(required=True))
        form.addAction(self._submit_addCategory,'add')
        return form

    def _submit_addCategory(self, ctx, form, data):
        def added(r):
            return url.URL.fromContext(ctx).replace('message', 'Category added successfully')
        def addError( failure ):
            failure.trap(error.NotUniqueError)
            raise xforms.FieldValidationError( 'duplicate textid', 'textid' )
        def catchUnauthorizedException(failure):
            failure.trap(capabilities.UnauthorizedException)
            u = url.URL.fromContext(ctx)
            sess.forceRollback = True
            return u.replace('errormessage', 'You do not have permission to update categories.')
        storeSession = util.getStoreSession(ctx)
        d = self.avatar.getCategoryManager(storeSession)
        d.addCallback(lambda categories: categories.addChildToNode(self.node, data['textid'], data['label']))
        d.addCallbacks(added,addError)
        d.addErrback(catchUnauthorizedException)
        return d


class EditableTreeNode(object):
    """
    Adapt a CategoryItem instance to the ICategoryItemTreeNode interface.
    """
    implements(IEditableTreeNode)

    def __init__(self, original):
        self.original = original

    def _getLabel(self):
        def renderer(ctx, data):
            nodeName = self.original.path.split('.')[-1]
            return T.a(href=url.here.child(nodeName))[self.original.label]
        return renderer

    value = property(lambda self: self.original.id)
    label = property(_getLabel)
    children = property(lambda self: self.original.children)


components.registerAdapter(EditableTreeNode, category.Category,
        IEditableTreeNode)
