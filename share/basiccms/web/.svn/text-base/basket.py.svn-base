from nevow import url, inevow, rend, accessors, tags as T
from crux import skin, icrux
import formal
from zope.interface import implements
from tub.public.web.common import getStoreSession
from basiccms import basket as dw_basket
from basiccms.web import common, checkout
import pollen.commerce.basket
from twisted.python.components import registerAdapter
from ecommerce.product.manager import Product
from pollen.mail import mailutil

from twisted.internet import defer

from ecommerce.salesorder.manager import SalesOrder, SalesOrderItem
from ecommerce.salesorder.util import createSalesOrderItem


class BasketPage(formal.ResourceMixin, common.Page):


    docFactory = skin.loader('BasketPage.html')


    def __init__(self, avatar, basketURL):
        super(BasketPage, self).__init__()
        self.avatar = avatar
        self.basketURL = basketURL


    def helperFactory(self, ctx):

        def itemFromId(id):
            storeSession = getStoreSession(ctx)
            return self.avatar.getProduct(storeSession, id)

        return dw_basket.BasketResourceHelper(self.avatar, self.avatar.basket, self.basketURL,
                self.basketURL.child('checkout'), itemFromId)


    def child_thankyou(self, ctx):
        return checkout.ThankYouPage(self.avatar)


    def renderHTTP(self, ctx):
        request = inevow.IRequest(ctx)
        if request.method == 'POST':
            # Is the request directed to the basket?
            command = request.args.get('command', [None])[0]
            if command:
                return self.helperFactory(ctx).handlePOST(ctx, request.args)
        return super(BasketPage, self).renderHTTP(ctx)


    def fragment_basket(self, ctx, data):
        return self.helperFactory(ctx).render_basket(ctx, data)


    def form_details(self, ctx):

        form = formal.Form()
        form.addField('firstName', formal.String(required=True, strip=True))
        form.addField('lastName', formal.String(required=True, strip=True))
        form.addField('email', formal.String(required=True, strip=True))
        form.addField('phoneNumber', formal.String(required=True, strip=True))
        form.addField('billingAddress', formal.String(strip=True), widgetFactory=formal.TextArea, label='Address')
        form.addField('billingPostcode', formal.String(strip=True), label='Postcode')
        form.addField('billingCountry', formal.String(strip=True), label='Country')
        form.addField('message', formal.String(strip=True), widgetFactory=formal.TextArea)
        form.addAction(self._placeOrder, label="Send Enquiry")
        return form


    def _placeOrder(self, ctx, form, data):


        def buildSalesOrder(data, storeSession):
            def gotSalesOrder(salesOrder):
                data['sales_order'] = salesOrder
            d = self._buildSalesOrder(storeSession, data)
            d.addCallback(gotSalesOrder)
            return d

        def addSalesOrder(data, storeSession):
            return self.avatar.realm.salesOrders.add(storeSession, data['sales_order'])


        def sendConfirmOrderEmail(data, ctx):
            salesOrder = data['sales_order']

            def getEmailText():
                emailPage = ConfirmOrderEmail(salesOrder)
                emailPage.remember(icrux.ISkin(ctx), icrux.ISkin)
                return emailPage.renderSynchronously()

            fromAddress = self.avatar.realm.config['mailService']['fromEmail']
            toAddress = [salesOrder.customer_email,self.avatar.realm.config['mailService']['fromEmail']]
            htmlemail = getEmailText()
            msg = mailutil.createhtmlmail(fromAddress, toAddress, 'David Ward Order Confirmation', htmlemail)
            return self.avatar.realm.mailService.sendMessage(toAddress, fromAddress, msg)


        def success(data):
            salesOrder = data['sales_order']
            self.avatar.basket.emptyBasket()
            self.avatar.checkoutDetails = None
            return url.URL.fromString('/basket/thankyou').add('order_num', salesOrder.order_num).add('basket_value', salesOrder.total_price).add('item_count', len(salesOrder.items))
            #return url.URL.fromContext(ctx).up().sibling('thankyou').add('order_num', salesOrder.order_num).add('basket_value', salesOrder.total_price).add('item_count', len(salesOrder.items))


        def failed(failure, data):
            raise formal.FormError('Unexpected error, please contact us on 0845 120 1036.')
        
        data['basket'] = self.avatar.basket
        storeSession = getStoreSession(ctx)
        d = buildSalesOrder(data, storeSession)
        d.addBoth(debug, 'after buildSalesOrder')
        d.addCallback(lambda ignore: addSalesOrder(data, storeSession))
        d.addBoth(debug, 'after addSalesOrder')
        d.addCallback(lambda ignore: sendConfirmOrderEmail(data, ctx))
        d.addBoth(debug, 'after addConfirmEmail')
        d.addCallback(lambda ignore: success(data))
        return d


    def _buildAddress(self, data, *attrs):
        tmp = []
        for attr in attrs:
            value = data.get(attr)
            if value:
                tmp.append(value)
        return '\n'.join( tmp )




    @defer.deferredGenerator
    def _buildSalesOrder(self, storeSession, data):
        checkOutDetails = data
        basket = self.avatar.basket
        billingAddress = checkOutDetails['billingAddress']
        deliveryAddress = checkOutDetails['billingAddress']

        deliveryName = '%s %s'%(checkOutDetails['firstName'], checkOutDetails['lastName'])
        deliveryAddress = billingAddress 
        deliveryPostcode = checkOutDetails['billingPostcode']
        deliveryCountry = checkOutDetails['billingCountry']

        salesOrder = SalesOrder(
            total_price = basket.getTotalPrice(),
            customer_id='1',
            customer_version='1',
            customer_first_name=checkOutDetails['firstName'],
            customer_last_name=checkOutDetails['lastName'],
            customer_address=billingAddress,
            customer_postcode=checkOutDetails['billingPostcode'],
            customer_country=checkOutDetails['billingCountry'],
            customer_phone_number=checkOutDetails['phoneNumber'],
            customer_email=checkOutDetails['email'],
            delivery_name=deliveryName,
            delivery_address=deliveryAddress,
            delivery_postcode=deliveryPostcode,
            delivery_country=checkOutDetails['billingCountry'],
            message=checkOutDetails['message'])

        for item in basket.getBasketItems():
            d = createSalesOrderItem(self.avatar, storeSession, item)
            d = defer.waitForDeferred(d)
            yield d
            salesOrderItem = d.getResult()
            salesOrder.addItem(salesOrderItem)

        yield salesOrder


class ThankYouPage(common.Page):

    docFactory = skin.loader('CheckoutThankYouPage.html')


    def __init__(self, avatar):
        super(ThankYouPage, self).__init__()
        self.avatar = avatar


    def render_order_num(self, ctx, data):
        order_num = inevow.IRequest(ctx).args.get('order_num', [''])[0]
        return order_num


class ConfirmOrderEmail(common.Page):
    docFactory = skin.loader('ConfirmOrderEmail.html')

    def __init__(self, salesOrder):
        super(ConfirmOrderEmail, self).__init__()
        self.salesOrder = salesOrder


    def data_sales_order(self, ctx, data):
        return accessors.ObjectContainer(self.salesOrder)


    def render_basket_item(self, ctx, basketItem): 
        #ctx.tag.fillSlots('thumbnail', T.img(src='/system/ecommerce/%s/mainImage?size=95x150&sharpen=1.0x0.5%%2b0.8%%2b0.1'%basketItem.original.product.id, class_='thumbnail'))
        ctx.tag.fillSlots('description', T.xml(basketItem.description))
        ctx.tag.fillSlots('unit_price', basketItem.unit_price)
        ctx.tag.fillSlots('quantity_ordered', basketItem.quantity_ordered)
        ctx.tag.fillSlots('total_price', basketItem.total_price)
        return ctx.tag



def debug(r, mess):
    print '>>DEBUG', mess, r
    return r
