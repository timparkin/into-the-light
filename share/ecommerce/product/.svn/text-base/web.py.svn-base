# -*- coding: utf8 -*-
from decimal import Decimal
import csv
import types
from cStringIO import StringIO
from twisted.internet import defer
from nevow import inevow, loaders, url, tags as T, static
from poop.objstore import NotFound
import formal
from cms.widgets import richtextarea
from tub.web import page, util, categorieswidget
from zope.interface import implements

from cms.widgets.richtext import FormalRichText, FormalRichTextArea, RichTextData
from cms import contenttypeutil

from pollen.nevow.tabular import tabular, cellrenderers, itabular

from ecommerce.product.optionmanager import OptionException


def loader(filename):
    return loaders.xmlfile(util.resource_filename('ecommerce.product.templates',
        filename), ignoreDocType=True)

MISSING = object()

def mapData(form, data, fromKeyFunc, toKeyFunc):
    """Map product data to and from formal data keys"""
    rv = {}

    def visitItem(node):
        fromName = fromKeyFunc(node)
        toName = toKeyFunc(node)

        value = data.get(fromName, MISSING)
        if value != MISSING:
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


def addProductFields(form, forCreation=False, restWriter=None, hasOptions=False):
    """
    Add product fields to a form.

    If forCreation is True then the main image will be a required field. This is
    to work around a limitation in Formal's file upload handling.
    """
    form.addField('code', formal.String(required=True, strip=True))
    form.addField('title', formal.String(required=True, strip=True))

    images = formal.Group('images')
    form.add( images )
    images.add( formal.Field('mainImage', formal.File(required=forCreation), 
        widgetFactory=formal.widgetFactory( formal.FileUploadWidget,
            convertibleFactory=contenttypeutil.KeyToFileConverter,
            originalKeyIsURL=True),description='click to change') )
    images.add( formal.Field('ndgrad', formal.File(), 
        widgetFactory=formal.widgetFactory( formal.FileUploadWidget,
            convertibleFactory=contenttypeutil.KeyToFileConverter,
            originalKeyIsURL=True),description='click to change') )


    availability = formal.Group('availability')
    form.add( availability )

    availability.add( formal.Field('show', formal.Boolean()))
    availability.add( formal.Field('available', formal.Boolean()) )
    availability.add( formal.Field('availabilityDescription', formal.String()) )

    metadata = formal.Group('metadata')
    form.add( metadata )

    metadata.add( formal.Field('date', formal.Date(), formal.widgetFactory(formal.DatePartsInput, dayFirst=True)))
    metadata.add( formal.Field('location', formal.String()) )
    
    lensOptions = [
        "72mm Schneider Super Angulon f5.6",
        "90mm Schneider Super Angulon f5.6",
        "150mm Schneider Apo-Symmar f5.6",
        "210mm Schneider Apo-Symmar f5.6",
        "270mm Nikon T*ED f6.3",
        "400mm Fujinon T f8"
    ]
    metadata.add( formal.Field('lens', formal.String(),formal.widgetFactory(formal.SelectOtherChoice, options=lensOptions)  ) )
    
    # this is a redundant field... need to remove if possible
    metadata.add( formal.Field('speedaperture', formal.String()) )
    
    speedOptions = ['1/500', '1/250','1/125','1/60','1/30','1/15','1/8','1/4','1/2','1s','2s','4s','8s','15s','30s','1m','2m']
    metadata.add( formal.Field('speed', formal.String(),formal.widgetFactory(formal.SelectOtherChoice, options=speedOptions),description='If you enter a text value please use the same format as the existing values e.g. 6s, 1/3, 2m' ) )
    
    
    apertureOptions = ['f/5.6','f/6.3','f/8','f/8⅓','f/8½','f/8⅔','f/16','f/16⅓','f/16½','f/16⅔','f/22','f/22⅓','f/22½','f/22⅔','f/32','f/32⅓','f/32½','f/32⅔','f/45','f/45⅓','f/45½','f/45⅔']
    metadata.add( formal.Field('aperture', formal.String(),formal.widgetFactory(formal.SelectOtherChoice, options=apertureOptions) ) )  
    metadata.add( formal.Field('tiltswing', formal.String()) )
    metadata.add( formal.Field('risefall', formal.String()) )
    ndfilters = ['0.3S','0.45S','0.6S','0.75S','0.9S','0.3H','0.45H','0.6H','0.75H','0.9H']
    metadata.add( formal.Field('ndfilters', formal.String(),formal.widgetFactory(formal.SelectOtherChoice, options=ndfilters)) )
    otherfilters=['81A','81B','81C','Polariser']
    metadata.add( formal.Field('otherfilters', formal.String(), formal.widgetFactory(formal.SelectOtherChoice, options=otherfilters)) )

    
    
    
    data_strings = [
        (0, '-'),
        (1, '*'),
        (2, '**'),
        (3, '***'),
        (4, '****'),
        (5, '*****'),
        ] 
    
    metadata.add( formal.Field('rating', formal.Integer(), formal.widgetFactory(formal.SelectChoice, options=data_strings)) )


    description = formal.Group('description')
    form.add( description )
    parsers = [('markdown','MarkDown'),('xhtml','XHTML'),('plain','Plain Text')]
    description.add( formal.Field('summary',  formal.RichTextType(required=True),
            widgetFactory=formal.widgetFactory(richtextarea.RichTextArea, parsers=parsers),
            cssClass=' '.join(['imagepicker','preview','itemselector']) ) )
    description.add( formal.Field('description', formal.RichTextType(required=True),
            widgetFactory=formal.widgetFactory(richtextarea.RichTextArea, parsers=parsers),
            cssClass=' '.join(['imagepicker','preview','itemselector']) ) )
    description.add( formal.Field('categories', formal.Sequence(formal.String()), 
        widgetFactory=categorieswidget.FormalCheckboxTreeMultichoice ) )



    if not hasOptions:
        pricing = formal.Group('pricing')
        form.add( pricing )
        pricing.add( formal.Field('price', formal.Decimal(required=True)) )


    seo = formal.Group('seo')
    form.add( seo )
    seo.add( formal.Field('titleTag', formal.String()) )
    seo.add( formal.Field('metaDescription', formal.String()) )
    seo.add( formal.Field('metaKeywords', formal.String()) )



def addStockFields(form):
    stock = formal.Group('stock', label='Stock Level')
    form.add( stock )
    stock.add(formal.Field('currentLevel', formal.Integer(immutable=True)))
    stock.add(formal.Field('adjustment', formal.Integer()))



def addOptionsFields(form, product=None, hasStock=False):
    description = ''
    if product and product.options:
        u = url.here.child('options.csv')
        description = T.p()[T.a(href=u)['Current Options CSV']]
    
    options = formal.Group('options', label='Options', description=description)
    form.add( options )
    options.add( formal.Field('optionsCSV', formal.File(), formal.FileUploadWidget))

    if product:
        for option in product.options:
            dataKey = 'options.'+option['code']
            group = formal.Group( option['code'], label=option['code'], 
                description=getOptionsStr(option) )
            options.add( group )
            group.add( formal.Field( 'price', formal.Decimal(required=True) ) )
            form.data[dataKey+'.price'] = option['price']

            if hasStock:
                group.add(formal.Field('currentLevel', formal.Integer(immutable=True)))
                form.data[dataKey+'.currentLevel'] = option['_stockLevel']
                group.add(formal.Field('adjustment', formal.Integer()))



@defer.deferredGenerator
def updateOptions(storeSession, manager, product, data):

    dataMap = {}

    csv = data.pop('options.optionsCSV')

    # Update price
    if product.options:

        for k, v in data.iteritems():
            ignore, code, attr = k.split('.')
            dataMap.setdefault(code,{})[attr] = v

        for option in product.options:
            optionData = dataMap.get(option['code'], {})
            price = optionData.get('price', MISSING)
            if price != MISSING:
                option['price'] = price


    # Read in new options/values from csv
    # These overwite any changes made on the screen
    try:
        # Load in new options CSV
        if csv:
            options = manager.getOptionManager().processFile(product.options, csv[1])
            product.options = options
    except OptionException, e:
        raise formal.FieldError(str(e), 'options.optionsCSV')

    # Update stock for ALL options
    for option in product.options:
        optionData = dataMap.get(option['code'], {})
        adjustment = optionData.get('adjustment')
        d = updateStock(storeSession, manager.getStockManager(), product.id, adjustment, optionCode=option['code'])
        d = defer.waitForDeferred(d) ; yield d
        d.getResult()
    
    # Tidy up stock records for options no longer required
    d = tidyStock(storeSession, manager.getStockManager(), product)
    d = defer.waitForDeferred(d) ; yield d
    d.getResult()
            


def getOptionsStr(option):
    cats = option['cats']
    rv = ['%s: %s'%(cat['cat'], cat['value']) for cat in cats]
    return ', '.join(rv)



def extractGroup(groupKey, data):
    rv = {}
    for k in data.keys():
        if k.startswith(groupKey):
            rv[k] = data.pop(k)
    return rv



def updateStock(storeSession, stockManager, productId, adjustment, optionCode=None):
    # This forces a stock record to be created (if there wasn't one already)
    # and the adjusts the stock level if an adjustment was specified).
    if not stockManager:
        return defer.succeed(None)

    if adjustment in (None, ''):
        adjustment = '0'
    adjustment = int(adjustment)

    d = stockManager.getCurrentLevel(storeSession, productId, option_code=optionCode)
    if adjustment:
        d.addCallback(lambda ignore: stockManager.adjustLevel(storeSession, productId, adjustment, option_code=optionCode))
    return d



def tidyStock(storeSession, stockManager, product):
    # Tidy up any stock records no longer required
    if not stockManager:
        return defer.succeed(None)

    optionCodes = []
    for option in product.options:
        optionCodes.append(option['code'])
    d = stockManager.tidyStock(storeSession, product.id, optionCodes)
    return d


class NewProductPage(formal.ResourceMixin, page.Page):

    componentContent = loader('NewProduct.html')

    def __init__(self, application):
        super(NewProductPage, self).__init__()
        self.application = application
        self.restWriter = self.application.restWriter


    def form_product(self, ctx):
        def buildForm(manager):
            form = formal.Form()
            addProductFields(form, forCreation=True, restWriter=self.restWriter)

            if manager.hasStockManager():
                addStockFields(form)
                form.data['stock.currentLevel'] = 0

            if manager.hasStockManager():
                addStockFields(form)


            form.addAction(self._submit)
            form.data['availability.available'] = True
            return form

        d = self.application.getManager()
        d.addCallback(buildForm)
        return d


    def _submit(self, ctx, form, data):

        storeSession = util.getStoreSession(ctx)


        def _updateStock(product, storeSession, manager, adjustment):
            d = updateStock(storeSession, manager.getStockManager(), product.id, adjustment)
            d.addCallback(lambda ignore: product)
            return d


        def addProduct(manager):
            d = manager.create(storeSession, data)
            d.addCallback(_updateStock, storeSession, manager, stockData.get('stock.adjustment'))
            return d


        def created(product):
            return url.URL.fromContext(ctx).sibling(product.id).replace('message', 'Product added successfully')


        stockData = extractGroup('stock.', data)
        data = getDataFromForm(form, data)

        d = self.application.getManager()
        d.addCallback(addProduct)
        d.addCallback(created)
        return d



class EditProductPage(formal.ResourceMixin, page.Page):

    componentContent = loader('EditProduct.html')

    def __init__(self, original, application):
        super(EditProductPage, self).__init__(original)
        self.application = application
        self.restWriter = self.application.restWriter

    def form_product(self, ctx):

        def buildForm(manager):
            form = formal.Form()
            if not hasattr(self.original,'speed'):
                self.original.speed = ''
            if not hasattr(self.original,'aperture'):
                self.original.aperture = ''
            addProductFields(form, hasOptions=self.original.hasOptions(), restWriter=self.restWriter)
            form.addAction(self._submit, label='Update Product Details' )
            putDataToForm( form, dict((attr,getattr(self.original,attr)) for attr in self.original._attrs),
                self.application.parent.services.getService(self.application.assetServiceName).getURLForAsset(self.original),
                self.original._assetNames)

            if manager.hasStockManager() and not self.original.hasOptions():
                # Only display stock if there are no options
                addStockFields(form)
                form.data['stock.currentLevel'] = self.original.getStockLevel()

            if manager.hasOptionManager():
                addOptionsFields(form, self.original, manager.hasStockManager())

            return form


        d = self.application.getManager()
        d.addCallback(buildForm)
        return d
            

    def _submit(self, ctx, form, data):
        storeSession = util.getStoreSession(ctx)

        def updated():
            return url.URL.fromContext(ctx).replace('message', 'Product updated successfully')

        def updateFailed(failure):
            failure.trap(NotFound)
            util.getStoreSession(ctx).forceRollback = True
            return url.URL.fromContext(ctx).replace('errormessage', 'Product update failed. Someone else has already changed the product.')

        def update(manager, data):


            def _updateStock(storeSession, stockManager, adjustment):
                # Only manage stock on the product directly if it has no options
                if not self.original.hasOptions():
                    d = updateStock(storeSession, stockManager, self.original.id, adjustment)
                    d.addCallback(lambda ignore: tidyStock(storeSession, stockManager, self.original))
                else:
                    d = defer.succeed(None)
                return d


            optionsData = extractGroup('options.', data)
            stockData = extractGroup('stock.', data)
            data = getDataFromForm(form, data)

            d = defer.succeed(None)
            if manager.hasOptionManager():
                # Check for and process options first
                d.addCallback(lambda ignore: updateOptions(storeSession, manager, self.original, optionsData))

            d.addCallback(lambda ignore: _updateStock(storeSession, manager.getStockManager(), stockData.get('stock.adjustment')))
            d.addCallback(lambda ignore: manager.update(self.original, data, storeSession))
            return d


        d = self.application.getManager()
        d.addCallback(update, data)
        d.addCallback(lambda ignore: storeSession.flush())
        d.addCallback(lambda ignore: updated())
        d.addErrback(updateFailed)
        return d


    def child_options_csv(self, ctx):
        def gotManager(manager):

            if manager.hasOptionManager():
                return static.Data(manager.getOptionManager().exportOptions(self.original.options), 'text/csv')
            else:
                return None

        d = self.application.getManager()
        d.addCallback(gotManager)
        return d
        


setattr(EditProductPage, 'child_options.csv', EditProductPage.child_options_csv)



class ProductTabularView(tabular.TabularView):
    docFactory = loader('ProductTabularView.html')

class ProductPage(formal.ResourceMixin, page.Page):
    """Page used for listing products and navigating to product instance editor. Also
    used to create and delete products.
    """
    componentContent = loader('Products.html')

    def __init__(self, application):
        super(ProductPage, self).__init__()
        self.application = application

    def child__submit(self,ctx):
        if inevow.IRequest(ctx).args.has_key('delete'):
            return self._submitDelete(ctx)
        if inevow.IRequest(ctx).args.has_key('updateCategories'):
            return self._submitUpdateCategories(ctx)
        return None
        
            

    def _submitDelete(self, ctx):
        sess = util.getStoreSession(ctx)

        # Get the list of product ids to delete from the form and
        ids = inevow.IRequest(ctx).args.get('id')
        if not ids:
            return url.URL.fromContext(ctx)

        def removeProduct(manager, id):
            d = manager.remove(sess, id)
            d.addCallback(lambda ignore: manager)
            return d

        def productsDeleted(spam):
            return url.URL.fromContext(ctx).replace('message', 'Products deleted successfully')

        d = self.application.getManager()
        for id in ids:
            d.addCallback(removeProduct, id)
        d.addCallback(lambda spam: sess.flush())
        d.addCallback(productsDeleted)
        return d

    @defer.deferredGenerator    
    def _submitUpdateCategories(self,ctx):
        sess = util.getStoreSession(ctx)

        # Get the list of product ids to delete from the form and
        args = inevow.IRequest(ctx).args
        items = {}

        
        
        for key, valList in args.items():
            if key.startswith('category-') and key.endswith('-val'):
                id = key[9:-4].split('-')[-1]
                cat = '-'.join(key[9:-4].split('-')[:-1])
                cat = cat.replace('1234567890','.')
                if valList[0] == 'False':
                    val = False
                else:
                    val = True
                items.setdefault(id,{}).setdefault(cat, {})['original'] = val
                items.setdefault(id,{}).setdefault(cat, {})['new'] = False

        for key, valList in args.items():
            if key.startswith('category-') and not key.endswith('-val'):
                id = key[9:].split('-')[-1]
                cat = '-'.join(key[9:].split('-')[:-1])
                cat = cat.replace('1234567890','.')
                items[id][cat]['new'] = True      
                
        for k,v in items.items():
            for K in v.keys():
                if not items[k][K].has_key('new'):
                    items[k][K]['new'] = False
        
                    
        # Now update the products that have changed
        itemsToUpdate = {}
        ncat = 0
        for id,v in items.items():
            for cat in v.keys():
                if items[id][cat]['original'] != items[id][cat]['new']:
                    ncat += 1
                    itemsToUpdate.setdefault(id,{})[cat] = items[id][cat]['new']
                else:
                    pass
        
        d = defer.waitForDeferred(self.application.getManager())
        yield d
        manager = d.getResult()
        
        for id,catVals in itemsToUpdate.items():
            d = defer.waitForDeferred(manager.findById(sess,id))
            yield d
            item = d.getResult()
            categories = item.categories
            if categories is None:
                categories = []
            for cat,val in catVals.items():
                if val is True:
                    categories.append(cat)
                else:
                    pos = categories.index(cat)
                    categories.pop(categories.index(cat))
            item.categories = categories
            item.touch()
                        
                
            
                
        yield url.URL.fromContext(ctx).replace('message', '%s categories updated'%ncat)
        return 
                
    def render_product_table_form(self, ctx, product):
        return ctx.tag(action=url.here.child('_submit'))

    def childFactory(self, ctx, id):
        # IDs are always ints
        try:
            id = int(id)
        except ValueError:
            return None

        def error(failure):
            failure.trap(NotFound)
            return None

        sess = util.getStoreSession(ctx)
        d = self.application.getManager()
        d.addCallback(lambda manager: manager.findById(sess, id))
        return d.addCallback(EditProductPage, self.application).addErrback(error)

    def render_newProduct(self, ctx, data):
        return ctx.tag(href=url.here.child('new'))

    def child_new(self, ctx):
        return NewProductPage(self.application)

    def form_search(self, ctx):

        form = formal.Form()
        form.data = {}
        form.addField('title', formal.String(),
            description="Enter the title of the product or partial title with wildcard '*'. e.g. '*Blue*' - case sensitive")
        form.addField('categories', formal.Sequence(formal.String()), 
            widgetFactory=categorieswidget.FormalCheckboxTreeMultichoice )

        if self.application.indexer is not None:
            form.addField('keyWords', formal.String())

        form.addAction(self._search, label='Search')

        form.data = self._getSearchCriteria(ctx)

        return form

    
    def form_inlineCategoryEdit(self, ctx):

        form = formal.Form()
        form.data = {}
        form.addField('ecategories', formal.Sequence(formal.String()), 
            widgetFactory=categorieswidget.FormalCheckboxTreeMultichoice )
        form.addAction(self._addCategories, label='Add These Categories')
        form.data = self._getCategoryCriteria(ctx)
        return form    

    def _addCategories(self, ctx, form, data):
        u = url.URL.fromContext(ctx)
        categories = data['ecategories']
        if categories in ( [], [''] ):
            categories = None
        if categories:
            u = u.replace('ecategories', '+'.join(categories))
        else:
            u = u.remove('ecategories')
        return u
            
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

    def _getCategoryCriteria(self,ctx):
        rv={}
        rv['ecategories'] = inevow.IRequest(ctx).args.get('ecategories', [None])[0]
        if rv['ecategories']:
            rv['ecategories'] = rv['ecategories'].split('+')        
        return rv
    
    def render_perPage(self,ctx,data):
        from nevow import tags as T
        options = ['20','50','100','300']
        wrapper = T.div(id='perPageOptions')
        wrapper['Item per Page: ']
        for option in options:
            wrapper[ T.a(href=url.gethere.replace('perPage',option))[ option ] ]
            wrapper[ ' ' ]
        return wrapper
        
        
        
    def render_product_table(self, ctx, data):
        perPage = int(inevow.IRequest(ctx).args.get('perPage', [20])[0])
        def gotModel(model):
            ecategories = inevow.IRequest(ctx).args.get('ecategories',[None])[0]
            if ecategories is not None:
                CATEGORIES = ecategories.split('+')
            else:
                CATEGORIES = []
            #['toy_type.art_and_craft','toy_type.books']
            for c in CATEGORIES:
                id = 'category-%s'%('1234567890'.join(c.split('.')))
                model.attributes[id] = tabular.Attribute(sortable=False)
                
            model.attributes['id'] = tabular.Attribute(sortable=False)
            model.attributes['code'] = tabular.Attribute(sortable=True)
            model.attributes['title'] = tabular.Attribute(sortable=True)

            view = ProductTabularView('products', model, perPage)
            view.columns.append(tabular.Column('id', '', 
                cellrenderers.CheckboxRenderer('id')))
            view.columns.append(tabular.Column('image', 'Image', 
                ImageRenderer('id')))
            view.columns.append(tabular.Column('code', 'Code', 
                cellrenderers.LinkRenderer(url.URL.fromContext(ctx), 'id' )))
            view.columns.append(tabular.Column('title', 'Title'))
            for c in CATEGORIES:
                id = 'category-%s'%('1234567890'.join(c.split('.')))
                view.columns.append(tabular.Column('id', T.a(href='#',title=c)['#'] , StoredStateCheckboxRenderer(id)))                

            return view

        storeSession = util.getStoreSession(ctx)
        d = self.application.getManager()
        d.addCallback(lambda manager: 
            manager.getTabularModel(storeSession, self._getSearchCriteria(ctx)))
        d.addCallback(gotModel)
        return d


    def render_csv_link(self, ctx, data):
        return ctx.tag(href=url.URL.fromContext(ctx).child('products.csv'))


    def child_products_csv(self, ctx):
        DECIMAL_ZERO = Decimal('0.00')

        def encodeValue(value):
            value = unicode(value or '').encode('utf8')
            return value

        def getAttrDict(product):
            rv = {}
            for attr in product._attrs:
                value = getattr(product,attr, None)

                if isinstance(value, RichTextData):
                    # Get the content out of Rich Text types
                    value = encodeValue(value.content)
                elif isinstance(value, (types.ListType, types.TupleType)):
                    # encode the items in the list
                    value = [encodeValue(v) for v in value if v]
                    if value == []:
                        value = encodeValue('')
                elif value and attr in ( 'mainImage'):
                    # create a url for images
                    value = '/system/ecommerce/%s/%s'%(product.id,attr)
                    value = encodeValue(value)
                elif isinstance(value, Decimal):
                    # Put pence into prices
                    value = value.quantize(DECIMAL_ZERO)
                    value = encodeValue(value)
                else:
                    value = encodeValue(value)

                rv[attr] = value

            return rv

        def gotProducts(products):
            fileData = StringIO()
            writer = None
            for product in products:
                if writer is None:
                    writer = csv.DictWriter(fileData, product._attrs, dialect="excel")
                    writer.writerow( dict([(a,a) for a in product._attrs]) )
                writer.writerow(getAttrDict(product))

            return static.Data(fileData.getvalue(), 'text/comma-separated-values')

        storeSession = util.getStoreSession(ctx)
        d = self.application.getManager()
        d.addCallback(lambda manager: manager.findMany(storeSession))
        d.addCallback(gotProducts)
        return d


setattr(ProductPage, 'child_products.csv', ProductPage.child_products_csv)


class StoredStateCheckboxRenderer(object):
    implements(itabular.ICellRenderer)

    def __init__(self, name, pattern=None):
        self.pattern = pattern or 'dataCell'
        self.name = name

    def rend(self, patterns, item, attribute):
        cell = patterns.patternGenerator(self.pattern)()
        id = item.getAttributeValue(attribute)
        tag = T.input(type="checkbox", name='%s-%s'%(self.name, id), value=id)
        value = item.getAttributeValue(self.name)
        if value:
            tag = tag(checked='checked')
        tag[ T.input(type='hidden', name='%s-%s-val'%(self.name, id), value=value) ]
        cell.fillSlots('value', tag)
        return cell
    
    

class ImageRenderer(object):
    implements(itabular.ICellRenderer)

    def __init__(self, name, pattern=None):
        self.pattern = pattern or 'dataCell'
        self.name = name

    def rend(self, patterns, item, attribute):
        cell = patterns.patternGenerator(self.pattern)()
        id = item.getAttributeValue(self.name)
        tag = T.img(src='/ecommerce/system/assets/%s/mainImage?size=60x60'%id)
        cell.fillSlots('value', tag)
        return cell
