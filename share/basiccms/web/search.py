import hype
from nevow import inevow, url, rend, tags as T
from crux import skin
from tub.public.web import common as tub_common
from twisted.internet import defer
from basiccms.web import common, products
import exceptions



class SearchPage(common.Page):
    docFactory = skin.loader('SearchPage.html', ignoreDocType=True)

    def __init__(self, avatar, productsURL, basketURL):
        super(SearchPage, self).__init__()
        self.avatar = avatar
        self.productsURL = productsURL
        self.basketURL = basketURL


    def data_static_results(self, section):

        def data_provider(ctx, data):
            query = inevow.IRequest(ctx).args.get('q', [''])[0]
            return getStaticPages(self.avatar, section, query)[:5]

        return data_provider


    def render_item(self, ctx, page):
        return StaticPageFragment(page)


    def data_products(self, ctx, data):

        keywords = inevow.IRequest(ctx).args.get('q', [''])[0]
        keywords = keywords.strip()

        if not keywords:
            return defer.succeed([])

        storeSession = tub_common.getStoreSession(ctx)
        d = self.avatar.getProducts(storeSession, keyWords=keywords)
        return d

    def render_admin(self,ctx,data):
        return ''    

    def render_products(self, ctx, data):

        storeSession = tub_common.getStoreSession(ctx)
        return products.ProductBrowserFragment( self.avatar, storeSession,
            self.productsURL, self.basketURL, data=data[:5])


    def render_if(self, ctx, data):
        return common.render_if(ctx, data)


    def render_more_link(self, section):

        def renderer(ctx, data):
            ctx.tag(href=url.URL.fromContext(ctx).child(section))
            return ctx.tag

        return renderer

    def render_q(self,ctx,data):
        keywords = inevow.IRequest(ctx).args.get('q', [''])[0]
        keywords = keywords.strip()
        return keywords
        


    def childFactory(self, ctx, name):
        if name == 'products':
            return ProductSearchPage(self.avatar, self.productsURL, self.basketURL)
        else:
            return StaticSearchPage(self.avatar, name)



class ProductSearchPage(common.Page):

    docFactory = skin.loader('ProductSearchPage.html', ignoreDocType=True)

    def __init__(self, avatar, productsURL, basketURL):
        super(ProductSearchPage, self).__init__()
        self.avatar = avatar
        self.productsURL = productsURL
        self.basketURL = basketURL


    def data_products(self, ctx, data):

        args = inevow.IRequest(ctx).args

        keywords = args.get('q', [''])[0]
        keywords = keywords.strip()

        if keywords == '':
            return defer.succeed([])

        storeSession = tub_common.getStoreSession(ctx)
        d = self.avatar.getProducts(storeSession, keyWords=keywords)
        return d


    def render_products(self, ctx, data):

        storeSession = tub_common.getStoreSession(ctx)
        return products.ProductBrowserFragment( self.avatar, storeSession,
            self.productsURL, self.basketURL, data=data)



class StaticSearchPage(common.PagingMixin, common.Page):

    docFactory = skin.loader('StaticSearchPage.html', ignoreDocType=True)

    def __init__(self, avatar, section):
        super(StaticSearchPage, self).__init__()
        self.avatar = avatar
        self.section = section


    def data_pages(self, ctx, data):
        query = inevow.IRequest(ctx).args.get('q', [''])[0]
        return getStaticPages(self.avatar, self.section, query)


    def render_item(self, ctx, page):
        return StaticPageFragment(page)


    def render_paging_controls_or_message(self, ctx, data):
        from basiccms.paging import IPagingData

        pagingData = ctx.locate(IPagingData)
        if pagingData.itemCount == 0:
            return inevow.IQ(ctx).onePattern('noData')
        else:
            return inevow.IQ(ctx).onePattern('hasData')

    def render_q(self,ctx,data):
        keywords = inevow.IRequest(ctx).args.get('q', [''])[0]
        keywords = keywords.strip()
        return keywords
        

class StaticIndex(object):

    def __init__(self, path):
        self.path = path


    def _openDatabase(self):
        return hype.Database(self.path)


    def _closeDatabase(self, db):
        db.close()


    def query(self, keyWords, section):
        rv = []
        db = self._openDatabase()
        try:
            try:
                s = db.search(unicode(keyWords), simple=False)
                s = s.add(unicode('@section iSTRINC %(section)s'%{'section':section}))
                rv = [(d['@uri'], d['@title'], d['@summary'],d['@content']) for d in s]
            finally:
                self._closeDatabase(db)
        except e:
            print e
        return rv


def getStaticPages(avatar, section, query):
    query = query.strip()
    if not query:
        return []

    index = StaticIndex(avatar.realm.config['indexes']['static'])
    rv = index.query(query, 'any')
    return rv



class StaticPageFragment(rend.Fragment):

    docFactory = skin.loader('StaticPageFragment.html')

    def __init__(self, page):
        self.page = page


    def render_item(self, ctx, data):
        u = url.URL.fromContext(ctx)
        u = url.URL(u.scheme, u.netloc, self.page[0].split('/')[1:])
        ctx.tag.fillSlots('path', self.page[0])
        ctx.tag.fillSlots('href', u)
        ctx.tag.fillSlots('title', self.page[1])
        q = ctx.arg('q')
        if q.lower() in self.page[3].lower():
            highspan = 50
            lowspan = 180
            wrapper = '<strong>%s</strong>'
            offset = self.page[3].lower().find(q.lower())
    
            import re
            cre=re.compile(q,re.IGNORECASE)
            if offset-lowspan <0:
                lower = 0
            else:
                lower = offset-lowspan
            if offset+highspan > len(self.page[3]):
                higher = len(self.page[3])
            else:
                higher = offset+highspan
            out = cre.sub(wrapper%q,self.page[3][lower:higher])
            ctx.tag.fillSlots('summary', T.xml(out))
        else:
            ctx.tag.fillSlots('summary', self.page[2])

        return ctx.tag


    def render_summary(self, ctx, data):
        if self.page[2]:
            return ctx.tag
        else:
            return ''
