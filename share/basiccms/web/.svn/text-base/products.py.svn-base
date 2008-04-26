from decimal import Decimal
from nevow import rend, url, tags as T, inevow, entities, appserver
from crux import skin
from twisted.internet import defer
from tub.public.web import pages as tub_pages
from tub.public.web.common import getStoreSession

from basiccms.web import common
from basiccms.web.utils import RenderFragmentMixin
from decimal import Decimal
import itertools



DECIMAL_ZERO = Decimal('0.00')


class ProductsResource(common.Page):


    def __init__(self, avatar, baseURL, basketURL):
        super(ProductsResource, self).__init__()
        self.avatar = avatar
        self.baseURL = baseURL
        self.basketURL = basketURL


    def renderHTTP(self, ctx):
        # For the case when I'm asked to render myself

        def gotItem(item):
            if item:
                return item
            else:
                return ProductsPage(self.avatar, None, self.basketURL)

        d = tub_pages.getSimpleItem(ctx, url.URL.fromContext(ctx).pathList())
        d.addCallback(gotItem)
        return d


    def locateChild(self, ctx, segments):
        # Load the CMS item, if present this is used as a last resort.
        # Wander down the segments tracking the category hierarchy
        # If I end at a leaf node then that is a product listing page.
        # If I end at a non leaf node, and I have a cms item use it, otherwise use a product listing page
        # If on my travels I find what looks like a product then use that.
        # If all else fails return a 404.

        def gotCategories(categories, data):
            data['categories'] = categories


        def gotCMSItem(item, data):
            data['item'] = item


        def returnResource(segments, data):
            filter = []

            # Start looking for categories in the pathList
            category = data['categories']
            productId = None
            remainingSegments = segments[:]
            for segment in segments:
                try:
                    # Does it look like a product?
                    productId = int(segment)
                except ValueError:
                    # Is is a category?
                    category = category.findChildByTextId(segment)

                if productId is not None:
                    remainingSegments = remainingSegments[1:]
                    break

                if category is None:
                    # Gone as far as I can
                    break

                remainingSegments = remainingSegments[1:]
                filter.append(('category', segment))


            if productId:
                return self._productPage(ctx, productId, remainingSegments)

            if category is None:
                if data['item']:
                    # No matching category, but CMS item, use CMS item
                    return inevow.IResource(data['item']), ()
                else:
                    # No matching category, and no CMS item, fail
                    return appserver.NotFound

            if category.children in (None, []):
                # Leaf category, product listing page
                return ProductsPage(self.avatar, None, self.basketURL, filter=filter), remainingSegments 

            # Non leaf category, use the CMS item, fall back to a product listing page
            if data['item']:
                return inevow.IResource(data['item']), ()
            else:
                return ProductsPage(self.avatar, None, self.basketURL, filter=filter),  remainingSegments


        data = {}

        cmsItemName = [i for i in itertools.chain(url.URL.fromContext(ctx).pathList(), segments)]

        storeSession = getStoreSession(ctx)
        d = self.avatar.realm.cmsService.loadCategories(storeSession, self.avatar, 'category')
        d.addCallback(gotCategories, data)
        d.addCallback(lambda ignore: tub_pages.getSimpleItem(ctx, cmsItemName))
        d.addCallback(gotCMSItem, data)
        d.addCallback(lambda ignore: returnResource(segments, data))
        return d


    def _productPage(self, ctx, productId, segments):

        # Find the product
        storeSession = getStoreSession(ctx)
        d = self.avatar.getProduct(storeSession, productId)

        # Create the resource for the product
        def createResource(product):
            if product is None:
                return None
            return ProductPage(self.avatar, product, self.basketURL, baseURL=self.baseURL), segments

        d.addCallback(createResource)
        return d



class ProductsPage(common.Page):


    docFactory = skin.loader('ProductsPage.html',ignoreDocType=True)


    def __init__(self, avatar, baseURL, basketURL, filter=None):
        super(ProductsPage, self).__init__()
        self.avatar = avatar
        self.baseURL = baseURL
        self.basketURL = basketURL
        self.filter = filter
        self.original = None


    def beforeRender(self, ctx):

        def gotItem(item):
            self.original = item

        d = self._getRelatedContentItem(ctx)
        d.addCallback(gotItem)
        return d


    def fragment_productBrowser(self, ctx, data):
        storeSession = getStoreSession(ctx)
        return ProductBrowserFragment(self.avatar, storeSession,
                self.baseURL, self.basketURL, self.filter)


    def render_related_content(self, ctx, data):

        if self.original is None:
            return ctx.tag.clear()

        ctx.tag.fillSlots('title', self.original.getAttributeValue('title', self.avatar.realm.defaultLanguage))
        ctx.tag.fillSlots('body', self.original.getAttributeValue('body', self.avatar.realm.defaultLanguage))
        ctx.tag.fillSlots('bodyFooter', self.original.getAttributeValue('bodyFooter', self.avatar.realm.defaultLanguage))
        return ctx.tag


    def _getRelatedContentItem(self, ctx):
        if self.filter is None:
            return defer.succeed(None)

        storeSession = getStoreSession(ctx)
        category = '.'.join( [self.filter[0][0]] +[c[1] for c in self.filter] )
        return self.avatar.realm.cmsService.getItem(storeSession, self.avatar, category=category)
    

    def parseSegments(self, segments):
        """
        Parse the segments to split the segments that look like facet-category
        pairs from those that don't.
        """
        filter = []
        remainingSegments = []
        for segment in segments:
            
            try:
                productId = int(segment)
            except ValueError:
                productId = None
 
            if productId is not None:
                remainingSegments.append( productId )
                break            
            
            
            splitSegment = segment.split('-', 1)
            if len(splitSegment) == 2:
                filter.append(splitSegment)
            else:
                filter.append( ('category',segment) )
        return filter, remainingSegments



class ProductPage(common.Page):


    docFactory = skin.loader('ProductPage.html',ignoreDocType=True)


    def __init__(self, avatar, product, basketURL, baseURL=None):
        super(ProductPage, self).__init__()
        self.avatar = avatar
        self.product = product
        self.basketURL = basketURL
        self.baseURL = baseURL


    def fragment_product(self, ctx, data):
        
        request = inevow.IRequest(ctx)
        zoom = request.args.get('zoom',[''])[0]
        if zoom == 'True':
            template = 'ProductFragmentZoom.html'
        else:
            template = 'ProductFragment.html'
            
        return ProductFragment(self.avatar, self.product,
                self.basketURL, template=template, baseURL=self.baseURL)


    def render_title(self, ctx, data):
        ctx.tag.clear()
        if self.product.titleTag:
            return ctx.tag[self.product.titleTag]
        else:
            return ctx.tag[self.product.title]


    def render_meta_description(self, ctx, data):
        if self.product.metaDescription:
            return ctx.tag(content=self.product.metaDescription)
        else:
            return super(ProductPage, self).render_meta_description(ctx, data)


    def render_meta_keywords(self, ctx, data):
        if self.product.metaKeywords:
            return ctx.tag(content=self.product.metaKeywords)
        else:
            return super(ProductPage, self).render_meta_keywords(ctx, data)



class ProductBrowserFragment(common.PagingMixin, RenderFragmentMixin, rend.Fragment):


    docFactory = skin.loader('ProductBrowser.html',ignoreDocType=True)
    fragmenttemplate = 'ProductSummaryFragment.html'
    

    def __init__(self, avatar, storeSession, baseURL, basketURL, filters=None, data=None, fragmenttemplate=None, browsertemplate=None):
        super(ProductBrowserFragment, self).__init__()
        self.avatar = avatar
        self.storeSession = storeSession
        self.baseURL = baseURL
        self.basketURL = basketURL
        self.filters = filters
        self.data = data
        if fragmenttemplate is not None:
            self.fragmenttemplate = fragmenttemplate

        if browsertemplate is not None:
            self.docFactory = skin.loader(browsertemplate)
        self.item = []


    def data_items(self, ctx, data):
        
        def byTitle(f, s):
            f = getattr(f,'title')
            s = getattr(s,'title')
            return cmp(f,s)

        def sort(items):
            items = list(items)
            items.sort(byTitle)
            return items

        if self.data is not None:
            return defer.succeed(self.data)       
        d = self.avatar.getProducts(self.storeSession, self.filters)
        d.addCallback(sort)
        return d


    def fragment_item(self, ctx, data):
        return ProductFragment(self.avatar, data, self.basketURL,
                template=self.fragmenttemplate,baseURL=self.baseURL)

        
    def render_chunkedrow(self,num):

        def renderer(ctx, data):
            tag = ctx.tag
            pattern = tag.patternGenerator('item')

            try:
                for d in data:
                    yield pattern( data=d )
            except:
                yield pattern(data=data)

        return renderer


    def render_paging_controls_or_message(self, ctx, data):
        from basiccms.paging import IPagingData

        pagingData = ctx.locate(IPagingData)
        if pagingData.itemCount == 0:
            return inevow.IQ(ctx).onePattern('noData')
        else:
            return inevow.IQ(ctx).onePattern('hasData')


    def render_chunked_sequence(self,num):

        chunksize = int(num)

        def render(ctx, data):
    
            tag = inevow.IQ(ctx).patternGenerator('item')

            accumulator = []
            for cnt,item in enumerate(data):
                if chunksize != 1:
                    accumulator.append(item)
                    if len(accumulator) == chunksize:
                        yield tag(data=accumulator)
                        accumulator = []
                else:
                    yield tag(data=item)
                    
            # yield remainder if there is any
            if len(accumulator) > 0:
                yield tag(data=accumulator)
    
        return render



class ProductFragment(rend.Fragment):


    def __init__(self, avatar, product, basketURL, template, baseURL=None):
        super(ProductFragment, self).__init__()
        self.avatar = avatar
        self.product = product
        self.basketURL = basketURL
        self.baseURL = url.here

        self.docFactory = skin.loader(template,ignoreDocType=True)


    def render_product(self, ctx, data):

        # Product id
        ctx.tag.fillSlots('id', self.product.id)

        # Product page link
        for c in self.product.categories:
            if c.startswith('gallery'):
                cat = c.split('.')[-1]
                break
            
        ctx.tag.fillSlots('url', url.URL.fromString('/gallery/%s/%s'%(cat,self.product.code)))

        # Simple string attributes
        for attr in ['code', 'title', 'summary','availabilityDescription']:
            ctx.tag.fillSlots(attr, getattr(self.product, attr) or '')

        # reST attributes
        for attr in ['description']:
            # XXX Convert to HTML
            ctx.tag.fillSlots(attr, getattr(self.product, attr))

        # Price attributes
        for attr in ['price']:
            ctx.tag.fillSlots(attr, getattr(self.product, attr))

        # Images
        for attr in [ 'mainImage']:
            ctx.tag.fillSlots(attr, getattr(self.product, attr))

        # Thumbnail image
        ctx.tag.fillSlots('thumbnailImage', 'mainImage')

        # Basket URL
        ctx.tag.fillSlots('basketURL', self.basketURL)

        # product URL
        ctx.tag.fillSlots('href', '')

        # img alt tags
        ctx.tag.fillSlots('alt', self.product.metaDescription or '')

        return ctx.tag

    
    def render_image1(self,ctx,data):
        image1 = getattr(self.product, 'image1')
        if image1 is not None:
            ctx.tag.fillSlots('id',self.product.id)
            return ctx.tag
        else:
            return ''

        
    def render_image2(self,ctx,data):
        image2 = getattr(self.product, 'image2')
        if image2 is not None:
            ctx.tag.fillSlots('id',self.product.id)
            return ctx.tag
        else:
            return ''
        

    def render_availability(self, ctx, data):
        if self.product.availabilityDescription is not None:
            return T.p(class_='availability')[T.strong['availability: '],self.product.availabilityDescription]
        else:
            return ''

        
    def render_price(self,ctx,data):
        price = self.product.getPrice()
        return T.span[ entities.pound, '%s' % price ]


        
    def render_totalPrice(self,ctx,data):

        price = self.product.getPrice()
        totalPrice = price
        return T.span[ entities.pound, '%s' % totalPrice ]

        
        
    def render_if(self, ctx, data):
        return common.render_if(ctx, data)


    def render_buy_button(self, ctx, data):
        return ''


    def data_hasPriceRange(self, ctx, data):
        return self.product.hasPriceRange()


    def render_options(self, ctx, data):

        if self.product.hasOptions():
            tag = inevow.IQ(ctx).onePattern('has_options')
        else:
            tag = inevow.IQ(ctx).onePattern('no_options')
        return tag


    def data_options(self, ctx, data):
        options = self.product.options
        return options


    def render_option(self, ctx, option):
        value = encodeOptionToId(self.product, option)
        description = getOptionDescription(option)
        price = self.product.getPrice(option=option)

        ctx.tag = ctx.tag(value=value)
        ctx.tag.fillSlots('description', description)
        ctx.tag.fillSlots('price', price)
        return ctx.tag



    def render_related_products(self, ctx, data):

        def gotProducts(products, storeSession):
            if products == []:
                return ''
            return ProductBrowserFragment(self.avatar, storeSession, self.baseURL, self.basketURL, data=products, fragmenttemplate='ProductSummaryFragment.html', browsertemplate='RelatedProductBrowser.html')

        relatedProducts = self.product.relatedProducts
        if relatedProducts is None:
            return ''
        codes = [c.strip() for c in relatedProducts.splitlines()]

        storeSession = getStoreSession(ctx)
        d = self.avatar.getProducts(storeSession, codes=codes)
        d.addCallback(gotProducts, storeSession)
        return d

        
    


