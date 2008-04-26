"""
E-commerce basket facility.
"""


# TODO
#
# * basket rules are not passed the basket. Makes sense for basket-global stuff,
#   i.e. delivery option.
# * Basket.addItem should not assume the IBasketItem adapter has an .original
#   attribute.
# * IBasketItem should have an isItTheSame method of some sort to test if an item
#   being added is already in the basket.
# * deferreds and things, i.e. persistent basket that is stored in the database
#   (which means deferred calls).


from zope.interface import implements, Interface
from twisted.python import components
from nevow import context, flat, inevow, rend, tags as T


##############
# Interfaces

class IBasket(Interface):
    """Interface for basket implementations that the renderer can
    understand.
    """
    def getBasketItems(self):
        """Return a sequence of basket items.
        """

    def getTotalPrice(self):
        """Get the basket's total price.
        """
        
class IBasketItem(Interface):
    """Basket items should have the following (readable) properties:

        uid: a unique id to identify an item by. uid is set by the basket
        item: item name
        unitPrice: the item's unit price (i.e. one of 'em)
        quantity: how many of the item are in the basket
    """

class IBasketRenderer(Interface):
    pass

class IBasketItemRenderer(Interface):
    pass

class IPriceRenderer(Interface):
    """Marker interface for a callable renderer that renders a basket
    price.
    """

class BasketRenderer:
    """Renders a basket and it items.
    """

    implements(IBasketRenderer, inevow.IRenderer)

    defaultBasket = T.table(_class='basket',border=0,cellpadding=0,cellspacing=0)
    defaultHeader = T.tr(_class='header')[
        T.th(_class='item')['Item'],
        T.th(_class='price unit')['Unit Price'],
        T.th(_class='quantity')['Quantity'],
        T.th(_class='price total')['Price'],
        ]
    defaultItem = T.tr(_class='item')[
        T.td(_class='item')[T.slot('item')],
        T.td(_class='price unit')[T.slot('unitPrice')],
        T.td(_class='quantity')[T.slot('quantity')],
        T.td(_class='price total')[T.slot('totalPrice')],
        ]
    defaultFooter = ''
    defaultTotal = T.tr(_class='total')[
        T.th(colspan=3)['Total'],
        T.td(_class='price')[T.slot('total')]
        ]
    defaultEmpty = T.tr(_class='empty')[
        T.td(colspan=4)['The basket is empty'],
        ]

    def __init__(self, basket):
        self.basket = basket

    def rend(self, ctx, data):

        try:
            renderPrice = ctx.locate(IPriceRenderer)
        except KeyError:
            renderPrice = lambda p: (T.xml('&pound;'),'%0.2f'%p)
            ctx.remember(renderPrice, IPriceRenderer)

        basket = self.defaultBasket.clone()

        def loadPattern(patternName, default):
            pattern = ctx.tag.allPatterns(patternName)
            if not pattern:
                pattern = default
            else:
                pattern = T.invisible[pattern]
            return pattern

        header = loadPattern('header', self.defaultHeader)
        footer = loadPattern('footer', self.defaultFooter)
        total = loadPattern('total', self.defaultTotal)
        empty = loadPattern('empty', self.defaultEmpty)
        itemPattern = inevow.IQ(ctx).patternGenerator('item', self.defaultItem)

        items = self.basket.getBasketItems()
        
        basket[header]
        if items:
            basket[ [itemPattern()(data=item, render=IBasketItemRenderer(item)) for item in items] ]
            total.fillSlots('total', renderPrice(self.basket.getTotalPrice()))
            basket[total]
        else:
            basket[empty]
        basket[footer]

        return basket


class BasketItemRenderer(rend.Fragment):
    '''Default basket item renderer.
    '''
    implements(IBasketItemRenderer, inevow.IRenderer)
    
    def rend(self, ctx, data):
        renderPrice = ctx.locate(IPriceRenderer)
        ctx.tag.fillSlots('uid', self.original.uid)
        ctx.tag.fillSlots('item', self.original.item)
        ctx.tag.fillSlots('quantity', self.original.quantity)
        ctx.tag.fillSlots('unitPrice', renderPrice(self.original.unitPrice))
        ctx.tag.fillSlots('totalPrice', renderPrice(self.original.quantity*self.original.unitPrice))
        return ctx.tag
        

############################################


def _itemUID():
    uid = 1
    while 1:
        yield uid
        uid += 1
        
itemUID = _itemUID()


class Basket:
    """Basic basket implementation.

    The basket keeps track of items and quantities of the items in the
    basket. It also applies any rules when a renderer asks for the
    basket items.
    """

    implements(IBasket)

    rules = []

    def __init__(self):
        self._items = []

    def addItem(self, item, quantity=1):
        if quantity <= 0:
            return
 
        for basketItem in self._items:
            if basketItem.original == item:
                break
        else:
            basketItem = IBasketItem(item)
            basketItem.uid = itemUID.next()
            self._items.append(basketItem)
            
        basketItem.quantity += quantity
        
    def getBasketItem(self, itemUID):
        for basketItem in self._items:
            if basketItem.uid == itemUID:
                return basketItem
 
    def removeItem(self, itemUID):
        for i, basketItem in enumerate(self._items):
            if basketItem.uid == itemUID:
                del self._items[i]
                break 

    def emptyBasket(self):
        self._items =[]

    def updateItemQuantity(self, itemUID, quantity):
        
        if quantity <= 0:
            self.removeItem(itemUID)
            return
        
        for basketItem in self._items:
            if basketItem.uid == itemUID:
                basketItem.quantity = quantity
                break
            
    def getBasketItems(self, rules=True):
        items = list(self._items)
        if rules:
            return self.applyRules(items)
        else:
            return items

    def getTotalPrice(self):
        totalPrice = 0
        for item in self.getBasketItems():
            totalPrice += item.unitPrice * item.quantity
        return totalPrice
    
    def applyRules(self, items):
        for rule in self.rules:
            try:
                items = rule(self, items)
            except TypeError, e:
                if rule.func_code.co_argcount != 1:
                    raise
                import warnings
                warnings.warn(
                        "[0.12.1] Basket rules now take two args. Please update %s."%rule,
                        DeprecationWarning)
                items = rule(items)
        return items
        
        
components.registerAdapter(BasketRenderer, Basket, IBasketRenderer)
components.registerAdapter(BasketItemRenderer, IBasketItem, IBasketItemRenderer)

