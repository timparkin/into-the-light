from zope.interface import Interface, implements
from twisted.internet import defer

class IProductIndexer(Interface):

    def add(product):
        """Add a product to the index"""

    def update(product):
        """Update the product in the index"""

    def remove(id):
        """Remove a product from the index"""

    def getMatchingIds(keyWords):
        """Return either None or a sequence (possibly empty) of product ids that match the keyWords"""

class NullProductIndexer(object):
    implements(IProductIndexer)

    def add(self, product):
        return defer.succeed(product)

    def update(self, product):
        return defer.succeed(product)

    def remove(self, id):
        return defer.succeed(id)

    def getMatchingIds(self, keyWords):
        return None
