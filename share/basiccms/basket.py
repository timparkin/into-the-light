from decimal import Decimal
from zope.interface import implements
from twisted.python.components import registerAdapter
from twisted.internet import defer
from nevow import inevow, stan, util as nevow_util, url, rend, tags as T

from pollen.commerce import basket as p_basket
from ecommerce import basket as e_basket
from ecommerce.product.manager import Product
from ecommerce.salesorder.util import ISalesOrderItemDataFactory, SalesOrderItemDataImpl, ISalesOrderItemData


DECIMAL_ZERO = Decimal('0.00')


def encodeOptionToId(product, option):
    if option:
        return '%s.%s'%(product.id, option['code'])
    else:
        return '%s'%product.id



def decodeOptionFromId(id):
    parts = id.split('.', 1)
    productId = parts[0]
    if len(parts) > 1:
        optionCode = parts[1]
    else:
        optionCode = None
    return productId, optionCode



def getOptionDescription(option):
    return ', '.join( [c['value'] for c in option['cats']])



class BasketItemEqualityHack(object):

    def __init__(self, obj):
        self.id = obj.id

    def __eq__(self, other):
        return self.id == other.id



class ProductBasketItem(object):

    implements(p_basket.IBasketItem)

    quantity = 0

    def __init__(self, productRef):
        self.productRef = productRef
        self.id = self.productRef.id

        self.categories = productRef.product.categories
        self.code = productRef.product.code

        self.item = self.productRef.getDescription()
        self.unitPrice = self.productRef.product.getPrice()
        if self.productRef.option:
            self.unitPrice = self.productRef.product.getPrice(option=self.productRef.option)

        self.original = BasketItemEqualityHack(self.productRef)



class ProductReference(object):
    def __init__(self, id, product, optionCode):
        self.id = id
        self.product = product
        self.option = None

        if optionCode:
            self.option = product.getOption(optionCode)


    def encodeToId(self):
        return encodeOptionToId(self.product, self.option)


    def getDescription(self):
        t = []
        for o in getOptionDescription(self.option).split(','):
            t.append(o)
            t.append(T.br())
        optionDescription = T.div[t[:-1]]
        if self.option:
            return [T.strong[self.product.title],T.br(),optionDescription]
        else:
            return T.strong[self.product.title]

registerAdapter(ProductBasketItem, ProductReference, p_basket.IBasketItem)







class BasketItemRenderer(rend.Fragment):
    implements(p_basket.IBasketItemRenderer)

    def rend(self, ctx, data):
        renderPrice = ctx.locate(p_basket.IPriceRenderer)
        # Product page link
        for c in self.original.categories:
            if c.startswith('gallery'):
                cat = c.split('.')[-1]
                break
            
        ctx.tag.fillSlots('url', url.URL.fromString('/gallery/%s/%s'%(cat,self.original.code)))        
        ctx.tag.fillSlots('id', self.original.id)
        ctx.tag.fillSlots('thumbnail', T.img(src='/system/ecommerce/%s/mainImage?size=95x150&sharpen=1.0x0.5%%2b0.8%%2b0.1'%self.original.productRef.product.id, class_='thumbnail'))
        ctx.tag.fillSlots('uid', self.original.uid)
        ctx.tag.fillSlots('item', self.original.item)
        if self.original.quantity > 1:
            ctx.tag.fillSlots('quantity', T.xml('x%s @ &pound;%0.2f each'%(self.original.quantity,self.original.unitPrice)))
        else:
            ctx.tag.fillSlots('quantity', '')
            
        ctx.tag.fillSlots('unitPrice', renderPrice(self.original.unitPrice))
        ctx.tag.fillSlots('totalPrice', renderPrice(self.original.quantity*self.original.unitPrice))
        return ctx.tag


registerAdapter(BasketItemRenderer, ProductBasketItem, p_basket.IBasketItemRenderer)


class ProductBasketItemSalesOrderItemDataFactory(object):
    implements(ISalesOrderItemDataFactory)


    def __init__(self, item):
        self.item = item


    def getData(self, avatar, storeSession):
        d = avatar.getProduct(storeSession, self.item.productRef.product.id)
        d.addCallback(self._gotProduct)
        return d


    def _gotProduct(self, product):
        code = product.code
        description = self.item.item

        if self.item.productRef.option:
            code += '.' + self.item.productRef.option['code']

        return SalesOrderItemDataImpl(code, description,
            self.item.quantity, self.item.unitPrice, 
            self.item.unitPrice * self.item.quantity, self.item.productRef.product.id)

registerAdapter(ProductBasketItemSalesOrderItemDataFactory,  ProductBasketItem, ISalesOrderItemDataFactory)








def getProductReferenceFromId(itemFromId, id):

    def gotProduct(product, optionCode):
        if not product:
            return None

        return ProductReference(id, product, optionCode)

    productId, optionCode = decodeOptionFromId(id)

    d = itemFromId(productId)
    d.addCallback(gotProduct, optionCode)
    return d



class BasketResourceHelper(e_basket.BasketResourceHelper):


    def __init__(self, avatar, basket, basketURL, checkoutURL, itemFromId):
        super(BasketResourceHelper, self).__init__(basket, basketURL, checkoutURL, self._itemFromId)
        self.avatar = avatar
        self._wrappedItemFromId = itemFromId



    def _itemFromId(self, id):
        # Wrap the passed itemFromId factory so I can handle options
        return getProductReferenceFromId(self._wrappedItemFromId, id)


    def command_add(self, ctx, args):
        """Hook in to update the delivery charges when something is
           added to an empty basket
        """

        return self._addToBasket(ctx, args)


    def _addToBasket(self, ctx, args):
        return super(BasketResourceHelper, self).command_add(ctx, args)





    def command_update(self, ctx, args):
        """Trap a request to remove a delivery basket item"""


        return super(BasketResourceHelper, self).command_update(ctx, args)




class Basket(p_basket.Basket):

    def __init__(self, avatar):
        p_basket.Basket.__init__(self)
        self.avatar = avatar
        self.rules = []



    def emptyBasket(self):
        return p_basket.Basket.emptyBasket(self)


