from decimal import Decimal
import codecs
import pkg_resources

from twisted.internet import defer
from nevow import loaders, url
import formal

from tub.web import page, util



def loader(filename):
    return loaders.xmlfile(util.resource_filename('ecommerce.delivery.templates',
        filename), ignoreDocType=True)



class DeliveryChargePage(formal.ResourceMixin, page.Page):
    """Page used for editing base delivery charges"""

    componentContent = loader('DeliveryCharge.html')


    def __init__(self, application):
        super(DeliveryChargePage, self).__init__()
        self.application = application


    def form_delivery_charge(self, ctx):

        def convert(data):
            if data is None:
                data = []
            return '\r\n'.join( [ ';'.join([str(i) for i in r]) for r in data ] )

        def buildForm(item):

            form = formal.Form()
            form.addField('countries', formal.String(required=True), widgetFactory=formal.TextArea)
            form.addField('rates', formal.String(required=True), widgetFactory=formal.TextArea)
            form.addAction(self._update, label='Update')

            form.data = {
                'countries': convert(item.countries),
                'rates': convert(item.rates)}

            return form

        storeSession = util.getStoreSession(ctx)
        d = self.application.getManager()
        d.addCallback(lambda manager: manager.find(storeSession))
        d.addCallback(buildForm)
        return d

    
    def _update(self, ctx, form, data):

        rates = self._getRates(data['rates'])
        charges = self._getCharges(rates, data['countries'])

        def gotManager(manager, storeSession):
            d = manager.find(storeSession)
            d.addCallback(gotItem, manager, storeSession)
            return d

        def gotItem(item, manager, storeSession):
            item.countries = charges
            item.rates = rates
            return manager.update(item, storeSession)

        storeSession = util.getStoreSession(ctx)
        d = self.application.getManager()
        d.addCallback(gotManager, storeSession)
        d.addCallback(lambda ignore: None)
        return d

    
    def _getRates(self, data):

        rv = {}
        line = 0
        for rateLine in data.splitlines():
            line = line + 1
            try:
                code, label, price = map(lambda x: x.strip(), rateLine.split(';'))
            except:
                raise formal.FieldError('Invalid format line %s'%line, 'rates')

            if rv.has_key(code.lower()):
                raise formal.FieldError('Duplicate code %s on line %s'%(code, line), 'rates')
            try:
                price = Decimal(price)
            except:
                raise formal.FieldError('Invalid price %s on line %s'%(price, line), 'rates')

            rv[code.lower()] = (code, label, price)

        rv = [ (v[0], v[1], v[2]) for v in rv.values() ]
        return rv


    def _getCharges(self, rates, data):

        rates = dict( [ (r[0], (r[1], r[2])) for r in rates ] )
        isoCodes = getISOCodes(self.application.countryCodeFileName)
        isoCodes = dict([(r[1].lower(),r[0]) for r in isoCodes])

        rv = []
        line = 0
        for rateLine in data.splitlines():
            line = line + 1
            try:
                # Try 'fr;zone1'
                country = None
                isoCode, rateCode = map(lambda x: x.strip(), rateLine.split(';'))
            except:
                try:
                    # Try 'france;fr;zone1'
                    country, isoCode, rateCode = map(lambda x: x.strip(), rateLine.split(';'))
                except:
                    # okay I give up
                    raise formal.FieldError('Invalid format line %s'%line, 'countries')

            isoCountry = isoCodes.get(isoCode.lower())
            if isoCountry is None:
                raise formal.FieldError('Unrecogised iso code %s on line %s'%(isoCode, line), 'countries')

            if country:
                if isoCountry.lower() != country.lower():
                    raise formal.FieldError('Unrecogised country %s for iso code %s on line %s'%(country, isoCode, line), 'countries')

            rate = rates.get(rateCode)
            if rate is None:
                raise formal.FieldError('Unrecogised rate code %s on line %s'%(rateCode, line), 'countries')

            rv.append((isoCountry, isoCode, rateCode))

        return rv


    def render_iso_codes(self, ctx, data):
        return ctx.tag(href=url.URL.fromContext(ctx).child('iso_codes'))


    def child_iso_codes(self, ctx):
        return ISOCountryCodesPage(self.application)


class ISOCountryCodesPage(page.Page):

    componentContent = loader('ISOCountryCodesPage.html')

    def __init__(self, application):
        self.application = application


    def data_iso_codes(self, ctx, data):
        rv = getISOCodes(self.application.countryCodeFileName)
        return rv


    def render_item(self, ctx, data):
        ctx.fillSlots('code', data[1])
        ctx.fillSlots('country', data[0])

        return ctx.tag


def getISOCodes(countryCodeFileName):
    rv = []
    f = codecs.open(countryCodeFileName, 'r')
    try:
        contents = f.read().splitlines()
        for l in contents:
            rv.append(l.split(';'))
    finally:
        f.close()
    return rv
