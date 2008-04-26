from zope.interface import Interface
from twisted.internet import defer
from nevow import flat

from ecommerce.salesorder.manager import SalesOrderItem

class ISalesOrderItemDataFactory(Interface):
    """Get an object that can return SalesOrderItemData"""

    def getData(avatar, storeSession):
        pass

class ISalesOrderItemData(Interface):
    """Get the data required sales order item"""

    def getCode():
        pass

    def getDescription():
        pass

    def getQuantity():
        pass

    def getUnitPrice():
        pass

    def getTotalPrice():
        pass

    def getItemId():
        pass


class SalesOrderItemDataImpl(object):

    def __init__(self, code, description, quantity, unitPrice, totalPrice, itemId):
        self.code = code 
        self.description = description 
        self.quantity = quantity 
        self.unitPrice = unitPrice
        self.totalPrice = totalPrice 
        self.itemId = itemId

    def getCode(self):
        return self.code

    def getDescription(self):
        return self.description

    def getQuantity(self):
        return self.quantity

    def getUnitPrice(self):
        return self.unitPrice

    def getTotalPrice(self):
        return self.totalPrice

    def getItemId(self):
        return self.itemId



@defer.deferredGenerator
def createSalesOrderItem(avatar, storeSession, item):
    d = _getSalesOrderItemData(avatar, storeSession, item)
    d = defer.waitForDeferred(d)
    yield d
    salesOrderItemData = d.getResult()

    rv = SalesOrderItem(
        code=salesOrderItemData.getCode(),
        description=str(flat.flatten(salesOrderItemData.getDescription())),
        quantity_ordered=salesOrderItemData.getQuantity(),
        unit_price=salesOrderItemData.getUnitPrice(),
        total_price=salesOrderItemData.getTotalPrice(),
        item_id=salesOrderItemData.getItemId()
        )
    yield rv



def _getSalesOrderItemData(avatar, storeSession, item):
    try:
        factory = ISalesOrderItemDataFactory(item)
    except TypeError:
        factory = None

    if factory:
        return factory.getData(avatar, storeSession)

    return defer.succeed(ISalesOrderItemData(item))




