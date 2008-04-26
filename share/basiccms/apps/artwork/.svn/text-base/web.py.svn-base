from itertools import imap

from twisted.internet import defer
from nevow import inevow, loaders, url
from poop.objstore import NotFound
import formal

from tub.web import page, util as tub_util, categorieswidget

from cms.widgets.richtext import FormalRichText, FormalRichTextArea
from cms import contenttypeutil

from pollen.nevow.tabular import tabular, cellrenderers

from basiccms.apps.artwork.widgets import SizeWidget


def loader(filename):
    return loaders.xmlfile(tub_util.resource_filename('basiccms.apps.artwork.templates',
        filename), ignoreDocType=True)

def mapData(form, data, fromKeyFunc, toKeyFunc):
    """Map artwork data to and from formal data keys"""
    rv = {}

    def visitItem(item):
        fromName = fromKeyFunc(item)
        toName = toKeyFunc(item)

        value = data[fromName]
        rv[toName] = value

    def visit(node):
        if hasattr(node, 'items'):
            for item in node.items:
                visit(item)
        else:
            visitItem(node)

    visit(form)
    return rv

def getDataFromForm( form, data ):
    return mapData(form, data, 
        lambda item: item.key,
        lambda item: item.key.rsplit('.', 1)[-1] )
    

def putDataToForm( form, data, baseURL, assetNames ):

    # Map the images to URLs for the widget
    def addSize(u):
        u = u.add('size', '160x120')
        u = u.add('nocache', 1)
        return u

    for asset in assetNames:
        data[asset] = addSize(baseURL.child(asset))

    form.data = mapData(form, data, 
        lambda item: item.key.rsplit('.', 1)[-1],
        lambda item: item.key)


def addArtworkFields(form, forCreation=False):
    """
    Add artwork fields to a form.

    If forCreation is True then the main image will be a required field. This is
    to work around a limitation in Formal's file upload handling.
    """


    form.addField('title', formal.String(required=True, strip=True))
    form.addField('longTitle', formal.String(strip=True))

    availability = formal.Group('availability')
    form.add( availability )

    availability.add( formal.Field('show', formal.Boolean()))
    availability.add( formal.Field('available', formal.Boolean()) )

    description = formal.Group('description')
    form.add( description )

    description.add( formal.Field('shortDescription', formal.String(strip=True),
            widgetFactory=formal.TextArea) )
    description.add( formal.Field('categories', formal.Sequence(), 
        widgetFactory=categorieswidget.FormalCheckboxTreeMultichoice ) )

    pricing = formal.Group('pricing')
    form.add( pricing )
    pricing.add( formal.Field('price', formal.Decimal(required=True)) )

    images = formal.Group('images')
    form.add( images )
    images.add( formal.Field('mainImage', formal.File(required=forCreation), 
        widgetFactory=formal.widgetFactory( formal.FileUploadWidget,
            convertibleFactory=contenttypeutil.KeyToFileConverter,
            originalKeyIsURL=True)) )

    seo = formal.Group('seo')
    form.add( seo )
    seo.add( formal.Field('titleTag', formal.String()) )
    seo.add( formal.Field('metaDescription', formal.String()) )
    seo.add( formal.Field('metaKeywords', formal.String()) )

class NewArtworkPage(formal.ResourceMixin, page.Page):

    componentContent = loader('NewArtwork.html')

    def __init__(self, application):
        super(NewArtworkPage, self).__init__()
        self.application = application

    def form_artwork(self, ctx):
        form = formal.Form()
        addArtworkFields(form, forCreation=True)
        form.addAction(self._submit)
        form.data['availability.show'] = True
        return form

    def _submit(self, ctx, form, data):

        sess = tub_util.getStoreSession(ctx)

        def created(artwork):
            return url.URL.fromContext(ctx).sibling(artwork.id).replace('message', 'Artwork added successfully')

        data = getDataFromForm(form, data)

        d = self.application.getManager()
        d.addCallback(lambda manager: manager.create(sess, data))
        d.addCallback(created)
        return d



class EditArtworkPage(formal.ResourceMixin, page.Page):

    componentContent = loader('EditArtwork.html')

    def __init__(self, original, application):
        super(EditArtworkPage, self).__init__(original)
        self.application = application

    def form_artwork(self, ctx):
        form = formal.Form()
        addArtworkFields(form)
        form.addAction(self._submit, label='Update Artwork Details' )
        putDataToForm( form, dict((attr,getattr(self.original,attr)) for attr in self.original._attrs),
            self.application.services.getService('assets').getURLForAsset(self.original),
            self.original._assetNames)

        return form

    def _submit(self, ctx, form, data):
        sess = tub_util.getStoreSession(ctx)

        def updated(artwork):
            return url.URL.fromContext(ctx).replace('message', 'Artwork updated successfully')

        def updateFailed(failure):
            failure.trap(NotFound)
            tub_util.getStoreSession(ctx).rollbackAlways = True
            return url.URL.fromContext(ctx).replace('errormessage', 'Artwork update failed. Someone else has already changed the artwork.')

        def update(ignore):
            d = self.application.getManager()
            d.addCallback(lambda manager: manager.update(self.original, data, sess) )
            return d

        data = getDataFromForm(form, data)

        d = defer.Deferred()
        d.addCallback(lambda ignore: update(data))
        d.addCallback(lambda ignore: sess.flush())
        d.addCallback(updated)
        d.addErrback(updateFailed)
        d.callback(None)
        return d

class ArtworkTabularView(tabular.TabularView):
    docFactory = loader('ArtworkTabularView.html')

class ArtworkPage(formal.ResourceMixin, page.Page):
    """Page used for listing artworks and navigating to artwork instance editor. Also
    used to create and delete artworks.
    """
    componentContent = loader('Artworks.html')

    def __init__(self, application):
        super(ArtworkPage, self).__init__()
        self.application = application

    def child__submitDelete(self, ctx):
        sess = tub_util.getStoreSession(ctx)

        # Get the list of artwork ids to delete from the form and
        ids = inevow.IRequest(ctx).args.get('id')
        if not ids:
            return url.URL.fromContext(ctx)

        def removeArtwork(manager, id):
            d = manager.remove(sess, id)
            d.addCallback(lambda ignore: manager)
            return d

        def artworksDeleted(spam):
            return url.URL.fromContext(ctx).replace('message', 'Artworks deleted successfully')

        d = self.application.getManager()
        for id in ids:
            d.addCallback(removeArtwork, id)
        d.addCallback(lambda spam: sess.flush())
        d.addCallback(artworksDeleted)
        return d

    def render_artwork_table_form(self, ctx, artwork):
        return ctx.tag(action=url.here.child('_submitDelete'))

    def childFactory(self, ctx, id):
        # IDs are always ints
        try:
            id = int(id)
        except ValueError:
            return None

        def error(failure):
            failure.trap(NotFound)
            return None

        sess = tub_util.getStoreSession(ctx)
        d = self.application.getManager()
        d.addCallback(lambda manager: manager.findById(sess, id))
        return d.addCallback(EditArtworkPage, self.application).addErrback(error)

    def render_newArtwork(self, ctx, data):
        return ctx.tag(href=url.here.child('new'))

    def child_new(self, ctx):
        return NewArtworkPage(self.application)

    def form_search(self, ctx):

        form = formal.Form()
        form.data = {}
        form.addField('title', formal.String(),
            description="Enter the title of the artwork or partial title with wildcard '*'. e.g. '*Blue*' - case sensitive")
        form.addField('categories', formal.Sequence(), 
            widgetFactory=categorieswidget.FormalCheckboxTreeMultichoice )

        if self.application.indexer is not None:
            form.addField('keyWords', formal.String())

        form.addAction(self._search, label='Search')

        form.data = self._getSearchCriteria(ctx)

        return form

    def _search(self, ctx, form, data):
        u = url.URL.fromContext(ctx)
        title = data['title']
        if title:
            u = u.replace('title', title)
        else:
            u = u.remove('title')

        categories = data['categories']
        if categories in ( [], [''] ):
            categories = None
        if categories:
            u = u.replace('categories', '+'.join(categories))
        else:
            u = u.remove('categories')

        if self.application.indexer is not None:
            keyWords = data['keyWords']
            if keyWords:
                u = u.replace('keyWords', keyWords)
            else:
                u = u.remove('keyWords')

        return u

    def _getSearchCriteria(self, ctx):
        rv = {}
        rv['title'] = inevow.IRequest(ctx).args.get('title', [None])[0]
        rv['categories'] = inevow.IRequest(ctx).args.get('categories', [None])[0]
        
        if rv['categories']:
            rv['categories'] = rv['categories'].split('+')

        rv['keyWords'] = inevow.IRequest(ctx).args.get('keyWords', [None])[0]

        return rv

    def render_artwork_table(self, ctx, ignore):
        data = {}

        def gotData(model):

            model.attributes['id'] = tabular.Attribute(sortable=False)
            model.attributes['title'] = tabular.Attribute(sortable=True)

            view = ArtworkTabularView('artworks', model, 20)
            view.columns.append(tabular.Column('id', '', 
                cellrenderers.CheckboxRenderer('id')))
            view.columns.append(tabular.Column('title', 'Title',
                cellrenderers.LinkRenderer(url.URL.fromContext(ctx), 'id' )) )

            return view

        storeSession = tub_util.getStoreSession(ctx)
        d = self.application.getManager()
        d.addCallback(lambda manager: 
            manager.getTabularModel(storeSession, self._getSearchCriteria(ctx)))
        d.addCallback(lambda model: gotData( model ))
        return d





    def child_system(self, ctx):
        return self.application.services

