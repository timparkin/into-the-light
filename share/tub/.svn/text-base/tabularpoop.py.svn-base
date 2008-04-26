from zope.interface import implements
from twisted.python.components import registerAdapter
from pollen.nevow.tabular import itabular
from poop import objstore



class PoopItemModel(object):
    """
    A generic implementation of a tabular Model for poop-persisted items. You
    are expected to subclass PoopItemModel to provide the model's attribute
    mapping and item type.
    """

    implements(itabular.IModel)


    itemType = None
    orderBy = None


    def __init__(self, storeSession, itemType=None, where=None, params=None):
        self.storeSession = storeSession
        if itemType is not None:
            self.itemType = itemType
        self.where = where
        self.params = params


    def setOrder(self, attribute, ascending):
        if attribute not in self.attributes:
            raise Exception("Illegal attribute")
        self.orderBy = "%s %s" % (attribute, ascending)


    def getItemCount(self):
        return self.getItems().addCallback(list).addCallback(len)


    def getItems(self, start=None, end=None):
        offset = start
        if end:
            limit = end-start
        else:
            limit = None
        return self.storeSession.getItems(itemType=self.itemType,
                where=self.where, params=self.params,
                orderBy=self.orderBy, offset=offset, limit=limit)



class PoopTabularItem(object):
    """
    Automatically get attributes from a poop item.

    Note: this is not secure, it allows *any* attribute to get retrieved, so
    ensure that names of attributes come from a safe source.
    """

    implements(itabular.IItem)

    
    def __init__(self, original):
        self.original = original


    def getAttributeValue(self, attribute):
        return getattr(self.original, attribute)


registerAdapter(PoopTabularItem, objstore.Item, itabular.IItem)

