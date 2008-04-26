import re

from zope.interface import implements
from twisted.python import components
from twisted.internet import defer
from poop import objstore
from pollen.nevow.tabular import itabular, tabular

from cms import icms
from cms.contenttypeutil import storeFile, getFile


class Customer(objstore.Item):
    
    __typename__ = 'ecommerce/customer'

    __table__ = 'customer'
    first_name = objstore.column()
    last_name = objstore.column()
    email = objstore.column()

    _attrs = (
        'email',
        'first_name', 'last_name', 
        'password',
        'phoneNumber', 
        'billingAddress1', 
        'billingAddress2', 
        'billingAddress3', 
        'billingCity', 
        'billingPostcode',
        'billingCountry',
        'optIn', 'terms',
        'gender',
        'dateOfBirth',
        'secretQuestion',
        'secretAnswer',
        )

    def __init__(self, *a, **kw):
        tmp = self._getAttrs(kw)
        super(Customer, self).__init__(*a, **kw)
        self._setAttrs(tmp)

    def _getAttrs(self, kw):
        rv = {}
        for attr in self._attrs:
            value = kw.pop(attr, None)
            rv[attr] = value

        rv['_crmData'] = kw.pop('crmData', None)
        return rv

    def _setAttrs(self, data):
        for key, value in data.iteritems():
            setattr(self, key, value)

        if self._crmData is None:
            self._crmData = {}

    def crmData():
        def getCRMData(self):
            return self._crmData

        def setCRMData(self, newCRMData):
            self._crmData = newCRMData

        return property(getCRMData, setCRMData)

    crmData = crmData()

    def name():
        def getName(self):
            return '%s, %s'%(self.last_name, self.first_name)

        return property(getName)

    name = name()


    def billingAddress():
        def getBillingAddress(self):
            return '\n'.join( [self.billingAddress1, self.billingAddress2 or '', 
                self.billingAddress3 or '', self.billingCity] )

        return property(getBillingAddress)
    billingAddress = billingAddress()
    

class CustomerTabularItem(object):
    implements(itabular.IItem)

    def __init__(self, customer):
        self.customer = customer

    def getAttributeValue(self, name):
        return getattr(self.customer, name)

components.registerAdapter(CustomerTabularItem, Customer, itabular.IItem)

class CustomerTabularModel(tabular.SequenceListModel):
    pass


class CustomerManager(object):

    def findById(self, storeSession, id):
        d = storeSession.getItemById(id)
        d.addCallback(self._getCRMData, storeSession)
        return d


    def findMany(self, storeSession, where=None, params=None):

        if where:
            where = ' and '.join( where )

        return storeSession.getItems(itemType=Customer, where=where,
                params=params, orderBy='last_name')


    def remove(self, storeSession, id):

        d = storeSession.removeItem(id)
        return d


    def create(self, storeSession, **kw):

        def flush(item, sess):
            d = sess.flush()
            d.addCallback(lambda ignore: item)
            return d

        d = storeSession.createItem(Customer, **kw)
        d.addCallback(flush, storeSession)
        d.addCallback(self.update, storeSession)

        return d


    def update(self, item, storeSession):

        item.touch()

        d = defer.succeed(None)
        d.addCallback(lambda ignore: self._storeCRMData(storeSession, item) )
        d.addCallback(lambda ignore: item)
        return d


    def getTabularModel(self, storeSession, criteria):

        class ParamKey(object):
            def __init__(self):
                self.number = 0

            def __call__(self):
                self.number = self.number + 1
                return 'param_%s'%self.number

        getParamNextKey = ParamKey()

        def addStringClause(column, value, where, params):
            paramKey = getParamNextKey()
            
            where.append( ' %s like %%(%s)s '%(column, paramKey) )
            params[paramKey] = value.replace('*', '%')

        where = []
        params = {}

        for column in ('last_name', 'first_name', 'email'):
            value = criteria.get(column, None)
            if value:
                addStringClause('customer.%s'%column, value, where, params)
            
        if where == []:
            where = None
            params = None

        d = defer.succeed(None)
        d.addCallback(lambda ids: self.findMany(storeSession, where, params))
        d.addCallback(lambda customers: CustomerTabularModel(list(customers))) 
        return d

    def _storeCRMData(self, storeSession, item):

        def addCRMKeyValuePair(ignore, key, value):
            return storeSession.curs.execute('insert into crm_data (id, key, value) values (%s, %s, %s)', (item.id,key,value))

        d = storeSession.curs.execute('delete from crm_data where id=%s', (item.id,))

        for key, value in item.crmData.iteritems():
            if not key:
                continue
            if not value:
                value = ''
            d.addCallback(addCRMKeyValuePair, key, value)

        return d

    def _getCRMData(self, item, storeSession):
        if item is None:
            return defer.succeed(None)

        def gotCRMData(rows):
            tmp = dict([(row[0],row[1]) for row in rows])
            item.crmData = tmp

            return item

        d = storeSession.curs.execute('select key, value from crm_data where id = %s', (item.id,))
        d.addCallback(lambda ignore: storeSession.curs.fetchall())
        d.addCallback(gotCRMData)
        return d

def debug(r, mess):
    print '>>DEBUG', mess, r
    return r
