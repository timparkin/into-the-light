import urllib
from zope.interface import implements
from twisted.internet import defer
from twisted.web import client
from nevow import flat, inevow, loaders, rend, static, tags as T, url
import forms


ALWAYS_SUCCEED = 100
ALWAYS_FAIL = 101


class WorldPayCallbackResource(object):
    """
    A resource responsible for handling a WorldPay callback.

    An optional "callback password" can be provided. The same password should be
    configured in the WorldPay managament interface. If the callback password
    does not match that sent by WorldPay then the callback is assumed to be
    from an invalid source.

    You are expected to override this class and provide implementation of the
    purchaseConfirmed and purchaseCancelled methods.
    """

    implements(inevow.IResource)

    def __init__(self, password=None):
        self.password = password

    def locateChild(self, ctx, segments):
        return None, ()

    def renderHTTP(self, ctx):

        # We only ever get one value per arg
        args = {}
        for k, v in inevow.IRequest(ctx).args.iteritems():
            if v:
                args[k] = v[0]
            else:
                args[k] = None

        # Check the callback password
        if self.password is not None:
            password = args.pop('callbackPW', None)
            if password is None:
                raise Exception("Missing callback password")
            if password != self.password:
                raise Exception("Invalid callback password")

        # Extract the information we need from the response
        transStatus = args.get('transStatus')
        purchaseId = args.get('cartId')

        if transStatus == "Y":
            transId = args.get('transId')
            d = defer.maybeDeferred(self.purchaseConfirmed, ctx, purchaseId,
                    transId, args)
            d.addErrback(self._handlePurchaseException)
            return d
        else:
            d = defer.maybeDeferred(self.purchaseCancelled, ctx, purchaseId,
                    args)
            return d

    def _handlePurchaseException(self, failure):
        print failure
        return failure

    def purchaseConfirmed(self, ctx, purchaseId, transId, args):
        raise NotImplemented()

    def purchaseCancelled(self, ctx, purchaseId, args):
        raise NotImplemented()


class WorldPayTestResource(forms.ResourceMixin, rend.Page):

    docFactory = loaders.stan(T.html[T.body[T.directive('form worldpay')]])

    def __init__(self, config):
        super(WorldPayTestResource, self).__init__()
        self.config = config

    def locateChild(self, ctx, data):
        return (None, ())

    def form_worldpay(self, ctx):
        form = forms.Form()
        form.addField('name', forms.String(required=True))
        form.addField('address', forms.String(required=True), forms.TextArea)
        form.addField('postcode', forms.String())
        form.addField('country', forms.String(required=True))
        form.addField('countryString', forms.String(required=True))
        form.addField('tel', forms.String())
        form.addField('fax', forms.String())
        form.addField('email', forms.String(required=True))
        form.addField('delvName', forms.String())
        form.addField('delvAddress', forms.String(), forms.TextArea)
        form.addField('delvPostcode', forms.String())
        form.addField('delvCountry', forms.String(required=True))
        form.addField('delvCountryString', forms.String(required=True))
        # Magic stuff
        form.addField('desc', forms.String(required=True))
        form.addField('amount', forms.String(required=True))
        form.addField('transId', forms.String(required=True))
        form.addField('cardType', forms.String(required=True))
        form.addField('M_hash', forms.String(), forms.Hidden)
        form.addField('cartId', forms.String(required=True), forms.Hidden)
        # Actions
        form.addAction(self.simulateSuccess, 'succeed')
        form.addAction(self.simulateFailure, 'fail', validate=False)
        form.data = {
            'name': ctx.arg('name'),
            'address': ctx.arg('address'),
            'postcode': ctx.arg('postcode'),
            'country': ctx.arg('country'),
            'countryString': 'Country String',
            'tel': ctx.arg('tel'),
            'fax': ctx.arg('fax'),
            'email': ctx.arg('email'),
            'delvName': ctx.arg('name'),
            'delvAddress': ctx.arg('address'),
            'delvPostcode': ctx.arg('postcode'),
            'delvCountry': ctx.arg('country'),
            'delvCountryString': 'Delivery Country String',
            'desc': ctx.arg('desc'),
            'amount': ctx.arg('amount'),
            'transId': '12345',
            'cardType': 'Visa',
            'M_hash': ctx.arg('M_hash'),
            'cartId': ctx.arg('cartId'),
        }
        return form

    def simulateSuccess(self, ctx, form, data):
        callbackData = dict(data)
        callbackData['transStatus'] = 'Y'
        return self.callback(ctx, callbackData)

    def simulateFailure(self, ctx, form, data):
        callbackData = dict(data)
        callbackData['transStatus'] = 'N'
        return self.callback(ctx, callbackData)

    def callback(self, ctx, callbackData):

        # Copy the callback data and add common stuff
        callbackData = dict(callbackData)
        callbackData['instId'] = self.config['instid']

        # Make the callback absolute to this site if it looks relative
        callback = callbackURL(ctx, self.config['callback'])

        postdata = []
        for k,v in callbackData.items():
            postdata.append('%s=%s' % (urllib.quote_plus(k.encode('utf-8')),
                urllib.quote_plus((v or '').encode('utf-8'))))
        postdata = '&'.join(postdata)

        # POST the callback
        d = client.getPage(callback, method='POST', postdata=postdata,
                headers={'content-type': 'application/x-www-form-urlencoded'})

        # Catch and display response
        def displayCallbackResponse(response):
            return flat.flatten(T.html[T.body[T.pre[T.xml(response)]]])
        d.addCallback(displayCallbackResponse)

        return d


def callbackURL(ctx, callback):
    if callback is None:
        return None
    if callback[0] != '/':
        return callback
    return str(url.URL.fromContext(ctx).click(callback))


def createWorldPayForm(ctx, config, purchaseId, basketHash, totalPrice, description,
        cardholder, withDelivery=False, fixContact=False):

    def maxLength(src, length):
        return src[:length]

    # Check the purchase ID is not too long
    purchaseId = str(purchaseId)
    if purchaseId != maxLength(purchaseId, 255):
        raise Exception("purchaseId must be less than 255 characters")

    # Decode the test mode.
    testMode = config['testMode']
    if testMode is not None:
        if testMode.lower() == 'succeed':
            testMode = ALWAYS_SUCCEED
        else:
            testMode = ALWAYS_FAIL

    # Decide what callback URL to use, if any.
    callback = callbackURL(ctx, config.get('callback'))

    rv = T.form(action=config['url'], method="post")
    # Worldpay account access
    rv[T.input(type="hidden", name="instId", value=config["instid"])]
    if testMode is not None:
        rv[T.input(type="hidden", name="testMode", value=testMode)]
    # General basket stuff
    rv[T.input(type="hidden", name="cartId", value=purchaseId)]
    rv[T.input(type="hidden", name="amount", value="%0.2f"%totalPrice)]
    rv[T.input(type="hidden", name="currency", value="GBP")]
    rv[T.input(type="hidden", name="desc", value=description)]
    # Basket hash
    rv[T.input(type="hidden", name="M_hash", value=basketHash)]
    # Buyer's details
    rv[T.input(type="hidden", name="name", value=maxLength(cardholder.name, 40))]
    rv[T.input(type="hidden", name="address", value=maxLength(cardholder.address, 255))]
    rv[T.input(type="hidden", name="postcode", value=maxLength(cardholder.postcode, 12))]
    rv[T.input(type="hidden", name="country", value=cardholder.country)]
    rv[T.input(type="hidden", name="email", value=maxLength(cardholder.email,80))]
    # Enable entry of the delivery address
    if withDelivery:
        rv[T.input(type="hidden", name="withDelivery")]
    # The cardholder and delivery details can optionally be fixed.
    if fixContact:
        rv[T.input(type="hidden", name="fixContact")]
    # Callback override
    if callback is not None:
        rv[T.input(type="hidden", name="MC_callback", value=callback)]
    # A button to post the form to Worldpay
    rv[T.input(type="submit", value="Enter Payment Details")]

    return rv

