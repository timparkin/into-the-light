from pollen.mail import mailutil

from twisted.internet import defer
from twisted.python import log
from nevow import url, accessors, inevow, tags as T, rend
import formal
from crux import skin, icrux
from tub.public.web.common import getStoreSession

from ecommerce.salesorder.manager import SalesOrder, SalesOrderItem
from ecommerce.salesorder.util import createSalesOrderItem

from basiccms import basket as dw_basket
from basiccms.web import common
from basiccms.web.utils import RenderFragmentMixin, RenderInheritMixin





class DetailsPage(RenderInheritMixin, RenderFragmentMixin, common.Page):


    docFactory = skin.loader('CheckoutDetailsPage.html')


    def __init__(self, avatar):
        super(DetailsPage, self).__init__()
        self.avatar = avatar

    def getCountryOptions(self, storeSession):
        data = {}
        d = self.avatar.getDeliveryCountries(storeSession)
        d.addCallback(lambda options: data.update({'delivery': options}))
        d.addCallback(lambda ignore: self.avatar.realm.getBillingCountryOptions())
        d.addCallback(lambda options: data.update({'billing': options}))
        d.addCallback(lambda options: data)
        return d


    def form_details(self, ctx):
        storeSession = getStoreSession(ctx)
        d = self.getCountryOptions(storeSession)
        d.addCallback(lambda options: self._build_details_form(options['billing'], options['delivery']))
        return d


    def _build_details_form(self, billingCountryOptions, deliveryCountryOptions):

        form = formal.Form()
        form.addField('firstName', formal.String(required=True, strip=True))
        form.addField('lastName', formal.String(required=True, strip=True))
        form.addField('phoneNumber', formal.String(required=True, strip=True))
        form.addField('billingAddress1', formal.String(required=True, strip=True))
        form.addField('billingAddress2', formal.String(strip=True))
        form.addField('billingAddress3', formal.String(strip=True))
        form.addField('billingCity', formal.String(required=True, strip=True))
        form.addField('billingPostcode', formal.String(required=True, strip=True))
        form.addField('billingCountry', formal.String(required=True, strip=True),
            widgetFactory=formal.widgetFactory(formal.SelectChoice, options=billingCountryOptions) )
        form.addField('cardType', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, CommonData.Cards))
        form.addField('cardNumber', formal.String(required=True, strip=True))
        form.addField('cvv2', formal.String(required=True, strip=True), 
            label='Card Security Code',description='last three numbers on signature strip')
        form.addField('expiryDate', formal.Date(required=True), 
            formal.widgetFactory(formal.MMYYDatePartsInput), description='e.g. 12/05' ) 
        form.addField('issueNumber', formal.String(strip=True), 
            description='for maestro and switch only')
        form.addField('startDate', formal.Date(), 
            formal.widgetFactory(formal.MMYYDatePartsInput), description='for switch only' )

        delivery = formal.Group('delivery', label='Delivery Address', description="Only enter details here if the delivery address is different from the billing address above.")
        form.add( delivery )
        delivery.add( formal.Field('name', formal.String(strip=True)) )
        delivery.add( formal.Field('address1', formal.String(strip=True)))
        delivery.add( formal.Field('address2', formal.String(strip=True)))
        delivery.add( formal.Field('address3', formal.String(strip=True)))
        delivery.add( formal.Field('city', formal.String(strip=True)))
        delivery.add( formal.Field('postcode', formal.String(strip=True)) )
        delivery.add( formal.Field('country', formal.String(strip=True),
            widgetFactory=formal.widgetFactory(formal.SelectChoice, options=deliveryCountryOptions)) )

        message = formal.Group('message', label='Gift Message', description="If you have chosen to use our gift wrapping service you can specify a message here")
        form.add( message )
        message.add( formal.Field('message', formal.String(strip=True), widgetFactory=formal.TextArea) )

        form.addAction(self._confirm, label="Confirm Order")

        if self.avatar.checkoutDetails:
            form.data = self.avatar.checkoutDetails
        elif self.avatar.customer:
            form.data = {
                'firstName': self.avatar.customer.first_name,
                'lastName': self.avatar.customer.last_name,
                'phoneNumber': self.avatar.customer.phoneNumber,
                'billingAddress1': self.avatar.customer.billingAddress1,
                'billingAddress2': self.avatar.customer.billingAddress2,
                'billingAddress3': self.avatar.customer.billingAddress3,
                'billingCity': self.avatar.customer.billingCity,
                'billingPostcode': self.avatar.customer.billingPostcode,
                'billingCountry': self.avatar.customer.billingCountry,
            }

            if self.avatar.realm.config['ecommerce']['paymentGateway'].get('use_test_data', False):

                from datetime import date
                from dateutil.relativedelta import relativedelta

                form.data['cardType'] = 'VISA'
                form.data['cardNumber'] = '4111111111111111'
                form.data['cvv2'] = '432'
                form.data['expiryDate'] = date.today()+relativedelta(months=6)

        return form


    def _confirm(self, ctx, form, data):

        deliveryAddressSpecified = data['delivery.address1'] or data['delivery.address2'] or data['delivery.address3']
        if data['delivery.name'] or deliveryAddressSpecified or data['delivery.city'] \
            or data['delivery.postcode'] or data['delivery.country']:

            if not data['delivery.name']:
                raise formal.FieldError('All delivery details must be entered.', 'delivery.name')
            if not deliveryAddressSpecified:
                raise formal.FieldError('All delivery details must be entered.', 'delivery.address1')
            if not data['delivery.city']:
                raise formal.FieldError('All delivery details must be entered.', 'delivery.city')
            if not data['delivery.postcode']:
                raise formal.FieldError('All delivery details must be entered.', 'delivery.postcode')
            if not data['delivery.country']:
                raise formal.FieldError('All delivery details must be entered.', 'delivery.country')

        self.avatar.checkoutDetails = data

        if data['delivery.country']:
            if self.avatar.basket.deliveryOptions.getCurrentCountry() != data['delivery.country'].lower():
                raise formal.FieldError('Delivery country does not match basket delivery option.', 'delivery.country')
        else:
            if self.avatar.basket.deliveryOptions.getCurrentCountry() != data['billingCountry'].lower():
                raise formal.FieldError('Delivery country does not match basket delivery option.', 'billingCountry')

        return url.URL.fromContext(ctx).sibling('confirm')


class ThankYouPage(common.Page):

    docFactory = skin.loader('CheckoutThankYouPage.html')


    def __init__(self, avatar):
        super(ThankYouPage, self).__init__()
        self.avatar = avatar


    def render_order_num(self, ctx, data):
        order_num = inevow.IRequest(ctx).args.get('order_num', [''])[0]
        return order_num


    def render_tracking(self, ctx, data):
        order_num = inevow.IRequest(ctx).args.get('order_num', [''])[0]
        basket_value = inevow.IRequest(ctx).args.get('basket_value', [''])[0]

        ctx.tag.fillSlots('order_num', order_num)
        ctx.tag.fillSlots('basket_value', basket_value)

        return ctx.tag


def debug(r, mess):
    print '>>DEBUG', mess, r
    return r
