# References:
#    https://www.secpay.com/xmlrpc/

from xml.sax import saxutils
from twisted.web import xmlrpc

class Card:

    def __init__(self, number, expiryDate, startDate=None, issue=None):
        self.number = number
        self.expiryDate = expiryDate
        self.startDate = startDate
        self.issue = issue

class Address:
    
    def __init__(self, name, telephone=None, email=None,
                 address1=None, address2=None, city=None, state=None,
                 country=None, postCode=None, company=None, url=None):

        if telephone is None and email is None:
            raise TypeError('You must provide at least one of telephone and email')
        
        self.name = name
        self.telephone = telephone
        self.email = email
        self.address1 = address1
        self.address2 = address2
        self.city = city
        self.state = state
        self.country = country
        self.postCode = postCode
        self.company = company
        self.url = url

    def toXML(self):

        args = ['name', 'telephone', 'email', 'address1', 'address2',
                'city', 'state', 'country', 'postCode', 'company',
                'url']
        args = dict([
            (arg,saxutils.escape(getattr(self,arg) or ''))
            for arg in args
            ])
        
        return '''<shipping class="com.secpay.seccard.Address">
            <name>%(name)s</name>
            <company>%(company)s</company>
            <addr_1>%(address1)s</addr_1>
            <addr_2>%(address2)s</addr_2>
            <city>%(city)s</city>
            <state>%(state)s</state>
            <country>%(country)s</country>
            <post_code>%(postCode)s</post_code>
            <tel>%(telephone)s</tel>
            <email>%(email)s</email>
            <url>%(url)s</url>
        </shipping>''' % args

class Order:

    def __init__(self):
        self.items = []

    def addItem(self, productCode, unitPrice, quantity):
        self.items.append((productCode, unitPrice, quantity))

    def toXML(self):

        itemsXml = []
        for item in self.items:
            itemsXml.append('''<OrderLine>
            <prod_code>%s</prod_code>
            <item_amount>%s</item_amount>
            <quantity>%s</quantity>
            </OrderLine>''' % (saxutils.escape(item[0]), item[1], item[2]))
            
        return '''<order class="com.secpay.seccard.Order">
            <orderLines class="com.secpay.seccard.OrderLine">
            %s
            </orderLines>
            </order>''' % itemsXml

class SECPayProxy:

    defaultOptions = {
        'mail_attach_customer': 'false',
        'mail_attach_merchant': 'false',
        }

    def __init__(self, merchantId, vpnPassword, test=False):
        self.merchantId = merchantId
        self.vpnPassword = vpnPassword
        if test:
            self.testStatus = 'true'
        else:
            self.testStatus = 'live'

    def transaction(self, transactionId, ip, name, card, amount,
               shippingAddress=None, billingAddress=None, order=None,
               **kw):

        options = dict(self.defaultOptions)
        options['test_status'] = self.testStatus
        options.update(kw)

        if shippingAddress is not None:
            shippingAddress = shippingAddress.toXML()

        if billingAddress is not None:
            billingAddress = billingAddress.toXML()

        if order is not None:
            order = order.toXML()

        args = [
            self.merchantId,
            self.vpnPassword,
            transactionId,
            ip,
            name,
            card.number,
            amount,
            card.expiryDate,
            card.issue or '',
            card.startDate or '',
            order or '',
            shippingAddress or '',
            billingAddress or '',
            ','.join(['%s=%s'%(k,v) for k,v in options.items()])
            ]

        args = [str(arg) for arg in args]
        
        def parseResponse(data):
            data = dict([kv.split('=') for kv in data[1:].split('&')])
            return data

        proxy = xmlrpc.Proxy('https://www.secpay.com/secxmlrpc/make_call')
        d = proxy.callRemote('SECVPN.validateCardFull', *args)
        return d.addCallback(parseResponse)


if __name__ == '__main__':

    import sys
    from twisted.internet import reactor
    from twisted.python import log
    
    log.startLogging(sys.stderr)

    def success(*value):
        print repr(value)
        reactor.stop()

    def error(failure):
        print 'ERROR', failure
        reactor.stop()

    order = Order()
    order.addItem('dubnobasswithmyheadman', 12.99, 2)

    SECPayProxy('secpay', 'secpay', True).transaction(
        '001',
        '127.0.0.1',
        'Matt Goodall',
        Card('4111111111111111', '12/05'),
        10.50,
        Address('Matt Goodall', email='matt.goodall@gmail.com', city='Leeds'),
        order = order,
        dups='false',
        mail_merchants='matt@pollenation.net',
        ).addCallbacks(success, error)

    reactor.run()
