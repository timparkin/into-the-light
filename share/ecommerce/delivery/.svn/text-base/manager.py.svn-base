
from twisted.internet import defer
from poop import objstore


EMPTY_DELIVERY_CHARGE_DATA = {
    'countries': [],
    'rates': []}


class DeliveryCharge(objstore.Item):

    __typename__= 'ecommerce/delivery'
    
    _attrs = (
        'countries',
        'rates')

    def __init__(self, *a, **kw):
        tmp = self._getAttrs(kw)
        super(DeliveryCharge, self).__init__(*a, **kw)
        self._setAttrs(tmp)


    def _getAttrs(self, kw):
        rv = {}
        for attr in self._attrs:
            value = kw.pop(attr, None)
            rv[attr] = value
        return rv


    def _setAttrs(self, data):
        for key, value in data.iteritems():
            setattr(self, key, value)



class DeliveryChargeException(Exception):
    pass



class DeliveryChargeManager(object):

    def find(self, storeSession):

        def gotItems(items):
            items = list(items)
            if not items:
                return self._create(storeSession)
            elif len(items) > 1:
                raise DeliveryChargeException('More than one set of delivery charges found')
            else:
                return defer.succeed(items[0])
            
        d = storeSession.getItems(itemType=DeliveryCharge)
        d.addCallback(gotItems)
        return d


    def _create(self, storeSession):


        def flush(item, sess):
            d = sess.flush()
            d.addCallback(lambda ignore: item)
            return d
        

        d = storeSession.createItem(DeliveryCharge, **EMPTY_DELIVERY_CHARGE_DATA)
        d.addCallback(flush, storeSession)
        return d


    def update(self, item, storeSession):
        item.touch()
        return defer.succeed(item)



def debug(r, mess):
    print '>>DEBUG', mess, r
    return r
