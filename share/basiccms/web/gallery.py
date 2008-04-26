from crux import skin, icrux
from basiccms.web import common
from tub.public.web import common as tubcommon
from basiccms import gallery
from nevow import tags as T, url, appserver, loaders, static
from ecommerce.product.manager import Product
import exceptions
from pollen.nevow import imaging

class Gallerys(common.Page):
    docFactory = skin.loader("Gallerys.html")


    def render_galleries(self,ctx,data): 
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)

        def gotCategories(categories):
            return avatar.realm.cmsService.getItems(storeSession, avatar, type=gallery.GalleryItem)

        def gotItems(items,categories):
            return avatar.getProducts(storeSession, categorisationFilters=[('flags','galleryindex')])
            
        def gotAll(items,categories,products):
            categoryCMSItems = {}
            for item in items:
                i = item.getProtectedObject()
                categoryCMSItems[i.name] = i

            categoryCMSItemMainImage = {}
            categoryCMSItemCode = {}
            for categoryCMSItem in categoryCMSItems.values():
                category = categoryCMSItem.name
                for product in products:
                    if u'gallery.%s'%category in product.categories: 
                        match = product
                        categoryCMSItemMainImage[categoryCMSItem.name] = match.id
                        categoryCMSItemCode[categoryCMSItem.name] = match.code
                        break

            htmlblock = []
            for n, category in enumerate(categories.children):
                name = category.textid
                categoryCMSItem = categoryCMSItems.get(name,None)
                column = divmod(n,3)[1]+1
                try: 
                    title = categoryCMSItem.title
                    shortDescription = categoryCMSItem.shortDescription
                except AttributeError:
                    title = category.label
                    shortDescription = ''
                
                try:
                    imgsrc='/system/ecommerce/%s/mainImage?size=190x300&sharpen=1.0x0.5%%2b0.7%%2b0.1'%categoryCMSItemMainImage[name]
                except KeyError:
                    imgsrc='/skin/images/spacer.gif'
                
                html = T.div(class_='category c%s'%column)[
                    T.a(href=url.here.child(name))[
                        T.img(src=imgsrc,width=190),T.span(class_='mbf-item')['#gallery %s'%categoryCMSItemCode[name]]
                        ],
                    T.h4[
                        T.a(href=url.here.child(name))[
                            title
                            ]
                        ],
                    T.p[
                        T.a(href=url.here.child(name))[
                            shortDescription
                        ]
                    ]
                ]
                htmlblock.append(html)
                # Group the output into threes
                if column == 3:
                    out = htmlblock
                    htmlblock = []
                    yield T.div(class_="threecolumnleft clearfix")[ out ]
            # and then yield anything left over if the last item wasn't at the end of a row
            if column != 3:
                yield T.div(class_="threecolumnleft clearfix")[ htmlblock ]

        d = avatar.realm.cmsService.loadCategories(storeSession, avatar,'gallery')
        d.addCallback(lambda categories: gotCategories(categories).addCallback(
            lambda items: gotItems(items,categories).addCallback(
                lambda products: gotAll(items,categories,products)
                )
              )
            )
        return d

    def render_title_tag(self, ctx, data):
        titleTag = 'Gallery'
        if titleTag:
            ctx.tag.clear()
            ctx.tag[titleTag]
        return ctx.tag    
    
    def childFactory(self, ctx, category):
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)
        def gotResult(result):
            categories = [r.textid for r in result.children]
            if category in categories:
                return Gallery(category,categories)
            
        if category == 'photos.rss':
            def gotProducts(products):
                return static.Data(str(getRss(products).encode('utf8')), 'text/xml')
            d = avatar.getProducts(storeSession)
            d.addCallback(gotProducts)
            return d
        
        d = avatar.realm.cmsService.loadCategories(storeSession, avatar, 'gallery')
        d.addCallback(gotResult)
        return d



class Gallery(common.Page):
    docFactory = skin.loader("Gallery.html")
    
    def __init__(self,category,categories):
        super(Gallery, self).__init__()
        self.category = category
        self.categories = categories
        
    def render_gallery(self,ctx,data):
        def gotProducts(products):
            htmlblock = []
            for n,product in enumerate(products):
                column = divmod(n,3)[1]+1
                name = product.code
                title = product.title
                shortDescription = product.summary
                imgsrc='/system/ecommerce/%s/mainImage?size=190x300&sharpen=1.0x0.5%%2b0.8%%2b0.1'%product.id
                
                html = T.div(class_='category c%s'%column)[
                    T.a(href=url.here.child(name))[
                        T.img(src=imgsrc,width=190),T.span(class_='mbf-item')['#gallery %s'%product.code]
                        ],
                    T.h4[
                        T.a(href=url.here.child(name))[
                            title
                            ]
                        ],
                    T.p[
                        T.a(href=url.here.child(name))[
                            shortDescription
                        ]
                    ]
                ]
                htmlblock.append(html)
                # Group the output into threes
                if column == 3:
                    out = htmlblock
                    htmlblock = []
                    yield T.div(class_="threecolumnleft clearfix")[ out ]
            # and then yield anything left over if the last item wasn't at the end of a row
            if column != 3:
                yield T.div(class_="threecolumnleft clearfix")[ htmlblock ]
 
                
        
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)
        d = avatar.getProducts(storeSession, categorisationFilters=[('gallery',self.category)])
        d.addCallback(gotProducts)
        return d    
    
    def render_admin(self,ctx,data):
        def gotGalleryItem(item):
            return T.div(id='admin')[ T.a(href=url.URL.fromString('http://admin.dw.timparkin.co.uk:8131/content/Gallery/%s'%item[0].getProtectedObject().id))[ 'Click here to edit gallery description' ] ]
            
        if common.isAdminOn(ctx):
            avatar = icrux.IAvatar(ctx)
            storeSession = tubcommon.getStoreSession(ctx)        
            d = avatar.realm.cmsService.getItems(storeSession, avatar, name=self.category, type=gallery.GalleryItem)
            d.addCallback(gotGalleryItem)
            return d            
        else:
            return ''    
    
    def render_gallerydescription(self,ctx,data):
        def gotGalleryItem(galleryItem):
            item = galleryItem[0].getProtectedObject()
            html = [
                T.div(class_="description")[
                    item.body
                    ],
                ]
            return html
                
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)        
        d = avatar.realm.cmsService.getItems(storeSession, avatar, name=self.category, type=gallery.GalleryItem)
        d.addCallback(gotGalleryItem)
        return d
    
    def render_gallerytitle(self,ctx,data):
        def gotGalleryItem(galleryItem):
            item = galleryItem[0].getProtectedObject()
            html = item.title
            return html
                
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)        
        d = avatar.realm.cmsService.getItems(storeSession, avatar, name=self.category, type=gallery.GalleryItem)
        d.addCallback(gotGalleryItem)
        return d    
    
    def render_galleries(self,ctx,data): 
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)

        def gotCategories(categories):
            return avatar.realm.cmsService.getItems(storeSession, avatar, type=gallery.GalleryItem)

        def gotItems(items,categories):
            categoryCMSItems = {}
            for item in items:
                i = item.getProtectedObject()
                categoryCMSItems[i.name] = i

            for n, category in enumerate(categories.children):
                name = category.textid
                categoryCMSItem = categoryCMSItems.get(name,None)
                column = divmod(n,3)[1]+1
                try: 
                    title = categoryCMSItem.title
                    shortDescription = categoryCMSItem.shortDescription
                except AttributeError:
                    title = category.label
                    shortDescription = ''
                
                html = [
                    T.h4[
                        T.a(href=url.here.up().child(name))[
                            title
                            ]
                        ],
                    T.p[
                        T.a(href=url.here.up().child(name))[
                            shortDescription
                        ]
                    ]
                ]
                yield html

        d = avatar.realm.cmsService.loadCategories(storeSession, avatar,'gallery')
        d.addCallback(lambda categories: gotCategories(categories).addCallback(
            lambda items: gotItems(items,categories)
              )
            )
        return d
 
    def data_products(self,ctx,data):
        def gotProducts(products):
            p = {}
            l = len(products)
            for n,category in enumerate(self.categories):
                if category == self.category:
                    p['prev'] = '/gallery/%s'%(self.categories[self.categories.index(self.category) - 1])
                    p['next'] = '/gallery/%s'%(self.categories[divmod(self.categories.index(self.category) + 1,len(self.categories))[1]])
            return p
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)
        d = avatar.getProducts(storeSession, categorisationFilters=[('gallery',self.category)])
        d.addCallback(gotProducts)
        return d
    
    def render_rssurl(self,ctx,data):
        return '/gallery/%s/photos.rss'%(self.category)
    
    def render_next(self,ctx,data):
        return T.a(href=data['next'])[ T.img(src='/skin/images/photonav-next%s.gif'%common.getInverted(ctx)) ]
    def render_prev(self,ctx,data):
        return T.a(href=data['prev'])[ T.img(src='/skin/images/photonav-prev%s.gif'%common.getInverted(ctx)) ]
    def render_up(self,ctx,data):
        return T.a(href='/gallery')[ T.img(src='/skin/images/photonav-up%s.gif'%common.getInverted(ctx)) ]
    

    def childFactory(self, ctx, photo):

        def gotProducts(products):
            if photo == '_first':
                return Photo(self.category,products[0],products[0].code,self.categories)
            if photo == '_last':
                return Photo(self.category,products[-1],products[-1].code,self.categories)
            if photo == 'photos.rss':
                return static.Data(str(getRss(products).encode('utf8')), 'text/xml')
        
                    
            
        def gotPhoto(product):
            return Photo(self.category,product,photo,self.categories)
            
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)
        if photo == '_first' or photo == '_last' or photo == 'photos.rss':
            d = avatar.getProducts(storeSession, categorisationFilters=[('gallery',self.category)])
            d.addCallback(gotProducts)
        else:
            d = avatar.getProductByCode(storeSession, code=photo)
            d.addCallback(gotPhoto)
        return d
    
XML_TEMPLATE = u"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<rss xmlns:media="http://search.yahoo.com/mrss" version="2.0" xmlns:n="http://nevow.com/ns/nevow/0.1">
    <channel>
      %s
 </channel>
</rss>      """
def getRss(products):
    item = u"""<item>
        <title>%s</title>
        <link>%s</link>
        <media:thumbnail url="%s"/>
        <media:content url="%s"/>
        <guid isPermaLink="false">%s</guid>
    </item>"""
    out = ''
    for p in products:
        code = p.code
        title = p.title
        title=title.replace('&','&amp;')
        title=title.replace('>','&gt;')
        title=title.replace('<','&lt;')
        url = None
        for c in p.categories:
            if c.startswith('gallery.'):
                url = '/%s/%s'%('/'.join(c.split('.')),p.code)
                break
        if url is None:
            url = '/gallery'
        imgsrc=u'/system/ecommerce/%s/mainImage?size=1199x1200&amp;sharpen=1.0x0.5%%2b0.8%%2b0.1&amp;quality=95'%p.id
        thumb =u'/system/ecommerce/%s/mainImage?size=601x631&amp;sharpen=1.0x0.5%%2b0.8%%2b0.1&amp;quality=60'%p.id
        out+=item%(title,url,thumb,imgsrc,code)
    return XML_TEMPLATE%out
            
            
            
    
    
    
class Photo(common.Page):
    
    docFactory = skin.loader("Photo.html")
    
    def __init__(self,category,photo,code,categories):
        super(Photo, self).__init__()
        self.category = category
        self.photo = photo
        self.categories = categories
        self.code = code

        
    def renderHTTP(self,ctx):
        large = ctx.arg('large',None)
        if large is not None:
            self.docFactory = skin.loader('Photo-zoom.html')
        return super(Photo, self).renderHTTP(ctx)
        
    def render_phototitle(self,ctx,data):
        return self.photo.title
    
    def render_admin(self,ctx,data):
        if common.isAdminOn(ctx):
            return T.div(id='admin')[ T.a(href=url.URL.fromString('http://admin.timparkin.co.uk:8131/ecommerce/product/%s'%self.photo.id))[ 'Click here to edit photo' ] ]
        else:
            return ''
    
    def render_photoinformation(self,ctx,data):
        
        p = self.photo
        

        
        priceoptions = []
        for optiondata in p.options:
            data={}
            for d in optiondata['cats']:
                data[d['cat']] = d['value']
            priceoptions.append(
                  {'name':optiondata['code'],'description':data['description'],'price':'%3.2f'%float(optiondata['price'])}
                )
        
        if p.date is not None:
            d = p.date.day
            if 4 <= d <= 20 or 24 <= d <= 30:
                suffix = "th"
            else:
                suffix = ["st", "nd", "rd"][d % 10 - 1]
                
            m = p.date.strftime('%B')
            y = p.date.strftime('%Y')
            day = '%s%s %s %s'%(d,suffix,m,y)
        else:
            day = '-'
        if p.location is not None:
            location = p.location
        else:
            location = '-'
        if p.lens is not None:
            lens = p.lens
        else:
            lens = '-'

        if hasattr(p,'speed') and p.speed is not None:
            speed = p.speed
        else:
            speed = '-'
        if hasattr(p,'aperture') and p.aperture is not None:
            aperture = p.aperture
        else:
            aperture = '-'
        if p.tiltswing is not None:
            tiltswing = p.tiltswing
        else:
            tiltswing = '-'
        if p.risefall is not None:
            risefall = p.risefall
        else:
            risefall = '-'
        if p.ndfilters is not None:
            ndfilters = p.ndfilters
        else:
            ndfilters = '-'
        if p.otherfilters is not None:
            otherfilters = p.otherfilters
        else:
            otherfilters = '-'

        hidecategorylist = ['flags']
            
        recorddata = [
            ('date', day),
            ('location', location),
            ('lens', lens),
            ('speed', speed),
            ('aperture', aperture),
            ('tilt/swing', tiltswing),
            ('rise/fall', risefall),
            ('nd filters', ndfilters),
            ('other filters', otherfilters),
            ('keywords',','.join( [ ':'.join(k.split('.')[1:]) for k in p.categories if k.split('.')[0] not in hidecategorylist] )),
            ]
            
        pricedl = T.dl()
        for option in priceoptions:
            pricedl[ T.dt[option['name']] ]
            pricedl[ T.dd[T.p[T.form(action='/basket',id='addtobasket',method='POST')[ T.input(type='hidden',name='id',value='%s.%s'%(self.photo.id,option['name'])),T.input(type='hidden',name='command',value='add'),T.input(type='submit',value='add') ],option['description']],T.p[T.xml('&pound;'),option['price']]] ]
        
        recorddl = T.dl()
        for key,value in recorddata:
            recorddl[ T.dt[key] ]
            recorddl[ T.dd[value] ]

        html = [
            T.invisible[ p.description ],
            T.div(class_="purchase clearfix")[
                T.h3(onclick="$('.purchase').BlindToggleVertically(500, null, 'easeout');$('#price a').toggleClass('over');return false;")['purchase options'],
                pricedl,
                ],
            T.div(class_="record clearfix")[
                T.h3(onclick="$('.record').BlindToggleVertically(500, null, 'easeout');$('#info a').toggleClass('over');return false;")['photographic record'],
                recorddl,
                ],
            ]
        return html
                
 
    
    
    def render_photo(self,ctx,data):
        
        def gotSize(size):
            quality = ctx.arg('quality')
            large = ctx.arg('large',None)
            if large is not None:            
                size = 'size=968x1200&'
                quality='100'
            else:
                size = 'size=600x632&'
            if quality is None:
                quality = '&quality=60'
                linkhref='?quality=93'
                enhance=T.p(class_='enhance')['click to enhance']
            else:
                quality = '&quality=100'
                linkhref='?large=True'
                enhance = T.p(class_='enhance')['click to see larger']

            if large is not None:
                enhance = T.p(class_='enhance')['click to return to small view']
                linkhref='?quality=93'
                
                
            if common.isInverted(ctx) is True:
                invert='&amp;invert=inverted'
            else:
                invert=''
            imgsrc='/system/ecommerce/%s/mainImage?%ssharpen=1.0x0.5%%2b0.8%%2b0.1%s%s'%(self.photo.id,size,quality,invert)
            html = T.a(class_='photo',href=linkhref)[ enhance,T.img(src=imgsrc) ]
            return html
        
        def gotAsset(path,imagingService):
            d = imaging.imagingService.getImageSize(path)
            d.addCallback(gotSize)
            return d
            
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)
        imagingService = avatar.realm.systemServices.getService('ecommerce')
        d = imagingService.getPathForAsset(avatar, storeSession, self.photo, 'mainImage', '')
        d.addCallback(gotAsset,imagingService)
        return d
    
    def data_products(self,ctx,data):
        def gotProducts(products):
            args = []
            large=ctx.arg('large',None)
            quality = ctx.arg('quality',None)
            if large is not None:
                args.append('large=%s'%large)
            if quality is not None:
                args.append('quality=%s'%quality)
            if len(args) > 0:
                args = '?%s'%('&'.join(args))
            else:
                args = ''
                
            
            p = {}
            l = len(products)
            for n,product in enumerate(products):
                if product.code == self.code:
                    if n == 0:
                        p['prev'] = '/gallery/%s/%s%s'%(self.categories[self.categories.index(self.category) - 1],'_last',args)
                    else:
                        p['prev'] = '/gallery/%s/%s%s'%(self.category,products[n-1].code,args)
                    if n+1 == l:
                        p['next'] = '/gallery/%s/%s%s'%(self.categories[divmod(self.categories.index(self.category) + 1,len(self.categories))[1]],'_first',args)
                    else:
                        p['next'] = '/gallery/%s/%s%s'%(self.category,products[n+1].code,args)
            return p
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)
        d = avatar.getProducts(storeSession, categorisationFilters=[('gallery',self.category)])
        d.addCallback(gotProducts)
        return d
    
    def render_next(self,ctx,data):
        return T.a(href=data['next'])[ T.img(src='/skin/images/photonav-next%s.gif'%common.getInverted(ctx)) ]
    def render_prev(self,ctx,data):
        return T.a(href=data['prev'])[ T.img(src='/skin/images/photonav-prev%s.gif'%common.getInverted(ctx)) ]
    def render_up(self,ctx,data):
        return T.a(href='/gallery/%s'%self.category)[ T.img(src='/skin/images/photonav-up%s.gif'%common.getInverted(ctx)) ]


    def render_category(self,ctx,data):
        def gotGalleryItem(galleryItem):
            return galleryItem[0].getProtectedObject().title
                
        avatar = icrux.IAvatar(ctx)
        storeSession = tubcommon.getStoreSession(ctx)        
        d = avatar.realm.cmsService.getItems(storeSession, avatar, name=self.category, type=gallery.GalleryItem)
        d.addCallback(gotGalleryItem)
        return d
    
    
