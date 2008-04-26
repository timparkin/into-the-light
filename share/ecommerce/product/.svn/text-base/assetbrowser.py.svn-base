import re
from nevow import rend, tags as T, loaders, inevow, context, url, accessors
import formal as forms
from cms import icms
from zope.interface import implements, Interface
from twisted.internet import defer
from twisted.python import components

from tub.web import categorieswidget, util

from cms import web
from crux import icrux
from pollen.nevow import imaging
from ecommerce.product.manager import Product


class AssetBrowser(rend.Page, forms.ResourceMixin):

    MAX_SIZE=170.0

    name = 'assetbrowser'

    docFactory = web.loader('AssetBrowser.html')

    def __init__(self, application, imageFactory=None):
        rend.Page.__init__(self )
        forms.ResourceMixin.__init__(self)

        self.application = application

        self.imageFactory = imageFactory
        if self.imageFactory is None:
            self.imageFactory = DefaultImageFactory(self.application)


    def form_search(self, ctx):
        categories = inevow.IRequest(ctx).args.get('categories', [])

        f = forms.Form()
        f.addField('categories', forms.Sequence(), widgetFactory=categorieswidget.CheckboxTreeMultichoice)
        f.addField('searchOwningId', forms.String(), forms.Hidden)
        f.addField('searchType', forms.String(), forms.Hidden)
        f.addField('format', forms.String(), forms.Hidden)

        args = inevow.IRequest(ctx).args

        owningId = args.get('searchOwningId',[''])[0]
        type = args.get('searchType',[''])[0]
        format = args.get('format',[''])[0]

        f.addAction(self._search, 'search')
        f.data = {
            'categories': categories,
            'searchOwningId': owningId,
            'searchType': type,
            'format': format,
        }
        return f


    def _search(self, ctx, form, data):
        categories = data.get('categories', [])
        u = url.URL.fromContext(ctx).clear()
        for c in categories:
            u = u.add('categories', c)
        return u


    def data_searchresults(self, ctx, data):

        args = inevow.IRequest(ctx).args

        query = args.get('categories', [''])

        avatar = icrux.IAvatar(ctx)
        storeSession = util.getStoreSession(ctx)
        d = self.imageFactory.getImages(avatar, storeSession, query)
        d.addCallback(self._setUpPaging, ctx)
        return d


    def _setUpPaging(self, data, ctx):

        args = inevow.IRequest(ctx).args
        pageno = args.get('pageno', [1])[0]
        pageno = int(pageno)
        query = args.get('categories', [''])

        if 'next' in args.keys():
            pageno += 1
        if 'previous' in args.keys():
            pageno -= 1

        if pageno < 0:
            pageno = 1

        pagesize = 6

        partpage = (data.count() % pagesize) and 1 or 0
        maxpageno = (data.count() / pagesize) + partpage

        if pageno > maxpageno:
            pageno = maxpageno

        start = (pageno - 1)*pagesize
        end = start + pagesize

        data.results = data.getData(start, end)
        data.pageno = pageno
        data.maxpageno = maxpageno
        data.query = query

        return data


    @defer.deferredGenerator
    def render_images(self, ctx, data):

        avatar = icrux.IAvatar(ctx)
        storeSession = util.getStoreSession(ctx)
        defaultLanguage = avatar.realm.defaultLanguage

        for image in data:

            asset, name = image

            d = self.imageFactory.getURL(avatar, storeSession, asset, name)
            d = defer.waitForDeferred(d)
            yield d
            imgURL = d.getResult()

            d = self.imageFactory.getSize(avatar, storeSession, asset, name)
            d = defer.waitForDeferred(d)
            yield d
            size = d.getResult()

            imgURL = imgURL.replace('size', '%dx%d'%(int(self.MAX_SIZE),int(self.MAX_SIZE)))
            margins = self._getMargins(size)
            altStr = self.imageFactory.getAltStr(asset)
            if altStr is None:
                altStr = ''
            # Replace white space with spaces, remove quotes
            altStr = re.sub('\s+', ' ', altStr)
            altStr = re.sub(""""|'""", '', altStr)

            tagGenerator = inevow.IQ(ctx.tag).patternGenerator('image')

            tag = tagGenerator()
            tag.fillSlots('id', asset.id)
            tag.fillSlots('src', imgURL)
            tag.fillSlots('style', "margin-left: %dpx; margin-top: %dpx"%(margins[0],margins[1]) )
            tag.fillSlots('alt', altStr)
            tag.fillSlots('onclick', "selectImage(this, '%s/%s','%s')"%(asset.id,name,altStr))

            ctx.tag[tag]

        yield ctx.tag

    def _getMargins(self, size):
        maxLength = max(size)
        if maxLength > self.MAX_SIZE:
            factor = self.MAX_SIZE/maxLength
            newSizes = [int(i*factor) for i in size]
        else:
            newSizes = size
        margins =  map(lambda newSize: int((self.MAX_SIZE - newSize)/2)+5, newSizes)
        return margins

    def render_results(self, ctx, data):
        if data.count() == 0:
            tag = inevow.IQ(ctx.tag).onePattern('nodocuments')
            yield tag
        else:
            tag = inevow.IQ(ctx.tag).onePattern('founddocuments')
            yield tag

        yield ctx.tag

    def render_navigationform(self, ctx, data):
        args = inevow.IRequest(ctx).args
        owningId = args.get('searchOwningId',[''])[0]
        type = args.get('searchType',[''])[0]
        format = args.get('format',[''])[0]
        ctx.tag = ctx.tag(action=url.URL.fromContext(ctx))
        ctx.tag.fillSlots('categories', data.query)
        ctx.tag.fillSlots('pageno', data.pageno)
        ctx.tag.fillSlots('searchOwningId', owningId)
        ctx.tag.fillSlots('searchType', type)
        ctx.tag.fillSlots('format', format)
        ctx.tag.fillSlots('contentType','gallery')
        return ctx.tag
    
    def render_pagingbuttons(self, ctx, data):
        if data.pageno > 1:
            tag = inevow.IQ(ctx.tag).onePattern('previouspage')
            yield tag
        if data.pageno < data.maxpageno:
            tag = inevow.IQ(ctx.tag).onePattern('nextpage')
            yield tag

class ListModel(object):
    def __init__(self, data):
        self.data = data

    def getData(self, start, end):
        return self.data[start:end]

    def count(self):
        return len(self.data)

components.registerAdapter(accessors.ObjectContainer, ListModel, inevow.IContainer)




class IImageFactory(Interface):
    def getURL(image):
        """Return the URL of the image"""

    def getSize():
        """Return the size of the image"""

    def getImages():
        """Return the images that match the query"""
        

class DefaultImageFactory(object):
    implements(IImageFactory)

    def __init__(self, application):
        self.application = application


    def getURL(self, avatar, storeSession, image, name):
        defaultLanguage = avatar.realm.defaultLanguage
        imgURL = self.application.services.getService('assets').getURLForAsset(image, defaultLanguage)
        if name:
            imgURL = imgURL.child(name)
        return defer.succeed(imgURL)


    def getSize(self, avatar, storeSession, image, name):
        defaultLanguage = avatar.realm.defaultLanguage

        d = self.application.services.getService('assets').getPathForAsset(avatar, storeSession, image, name, defaultLanguage)
        d.addCallback(imaging.imagingService.getImageSize)
        return d

    def getAltStr(self, asset):
        return ''

    def getImages(self, avatar, storeSession, query):

        def findImages(storeSession):

            def gotItems(items):
                items = list(items)
                if len(items):
                    return items
                else:
                    return []

            where = """ product.id in (
                select
                    distinct f.id
                from
                    file f
                    join product ci on f.id = ci.id
                where
                    mime_type like 'image%%'
                order by
                    id)
                """

            d = storeSession.getItems(itemType=Product, where=where)
            d.addCallback(gotItems)
            return d


        def gotAssets(assets, query): 

            rv = []
            for asset in assets:
                pickableAsset = icms.IPickableAsset(asset, None)
                if not pickableAsset:
                    continue
                if not displayAsset(asset, query):
                    continue
                for name in pickableAsset.pickableAssetNames:
                    rv.append((asset, name))
            return ListModel(rv)

        def displayAsset(asset, query):

            if query is None or query == [] or query == ['']:
                    return True
            assetCats = getattr(asset, 'categories', None)
            if assetCats is None or assetCats == [] or assetCats == ['']:
                return False

            for category in query:
                for assetCat in assetCats:
                    if assetCat.startswith(category):
                            return True
            return False


        d = findImages(storeSession)
        d.addCallback(gotAssets, query)
        return d


def debug(r, msg):
    print '>>DEBUG', msg, r
    return r

