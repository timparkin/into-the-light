import re

import formal
from formal import converters

from tub.web import categorieswidget

from ecommerce.voucher import base
from ecommerce.voucher.widgets import nfields

class Voucher(object):

    def getCreator(self):
        return CategorisedVoucherCreator()        


    def getEditor(self):
        return CategorisedVoucherEditor()        


    def getType(self):
        return CategorisedVoucherDefinition


    def getUpdateSQL(self):
        sql = """
            update %(table)s 
                set start_date=%%(start_date)s, end_date=%%(end_date)s, amount=%%(amount)s,
                lower_bound=%%(lower_bound)s, upper_bound=%%(upper_bound)s, categories=%%(categories)s
            where
                voucher_definition_id = %%(voucher_definition_id)s"""

        return sql



class CategorisedVoucherDefinition(base.BaseVoucherDefinition):

    _attrs = (
        'voucher_definition_id',
        'code',
        'count',
        'multiuse',
        'start_date',
        'end_date',
        'amount',
        'categories',
        'lower_bound',
        'upper_bound',
         )


AMOUNT_RE = re.compile( '^\d+(\.\d+)?%?$' )


def addFields(form, forCreate = False):

    if forCreate:
        codeField = formal.String(required=True, strip=True)
        countField = formal.Integer()
        multiuseField = formal.Boolean()
    else:
        codeField = formal.String(immutable=True)
        countField = formal.Integer(immutable=True)
        multiuseField = formal.Boolean(immutable=True)

    form.add( formal.Field('code', codeField) )

    form.add( formal.Field('categories', formal.Sequence(formal.String()), 
        widgetFactory=categorieswidget.FormalCheckboxTreeMultichoice ) )

    form.add( formal.Field('count', countField) )
    form.add( formal.Field('multiuse', multiuseField) )
    form.add( formal.Field('start_date', formal.Date()) )
    form.add( formal.Field('end_date', formal.Date()) )
    form.add( formal.Field('amount', formal.String(strip=True), description="Either an amount or a '%'") )

    form.add( formal.Field('mForN', formal.Sequence(formal.Integer), 
        widgetFactory=formal.widgetFactory(nfields.NFieldWidget, 2, ['for'])))

    return form

def boundsFromFormFields(bounds):

    converter = converters.IntegerToStringConverter(None)
    try:
        return dict(
            lower_bound = converter.toType(bounds[0]),
            upper_bound = converter.toType(bounds[1])
        )
    except formal.FieldValidationError, e:
        e.fieldName = 'mForN'
        raise e


def commonValidation(data):

    if (data['lower_bound'] or data['upper_bound']) \
        and not (data['lower_bound'] and data['upper_bound']):
        raise formal.FieldError( "Both bounds must be specified", 'mForN' )

    if (data['amount'] or data['lower_bound']) \
        and (data['amount'] and data['lower_bound']):
        raise formal.FieldError( "Only one of amount and m for n must be specified", 'amount' )

    if not (data['amount'] or data['lower_bound']):
        raise formal.FieldError( "One of amount or m for n must be specified", 'amount' )

    if data['amount'] and not AMOUNT_RE.match(data['amount']):
        raise formal.FieldError( "Unrecognised format", 'amount' )

    if data['lower_bound'] and data['lower_bound'] <= data['upper_bound']:
        raise formal.FieldError( "Lower bound must be bigger than upper bound", 'mForN' )


class CategorisedVoucherCreator(object):


    def addFields(self, form):
        addFields(form, forCreate = True)


    def create(self, ctx, form, inData):

        # So I don't mess up data
        data = {}
        data.update(inData)

        data.update(boundsFromFormFields(data['mForN']))
        data.pop('mForN')

        commonValidation(data)

        if not data['multiuse'] and not data['count']:
            raise formal.FormError( "One of 'multiuse' and 'count' must be specified" )

        if data['multiuse'] and data['count']:
            raise formal.FormError( "Only one of 'multiuse' and 'count' must be specified" )

        voucherDefinition = CategorisedVoucherDefinition(**data)
        if data['multiuse']:
            voucher = base.Voucher(code=data['code'])
            voucherDefinition.addVoucher(voucher)
        else:
            codes = base.generateCodes(data['code'], data['count'])
            for code in codes:
                voucher = base.Voucher(code=code)
                voucherDefinition.addVoucher(voucher)

        return voucherDefinition




class CategorisedVoucherEditor(object):


    def addFieldsAndData(self, form, voucherDefinition):
        addFields(form)
        form.data = voucherDefinition.getDataDict()
        form.data.update(self._boundsToFormFields(voucherDefinition))


    def _boundsToFormFields(self, voucherDefinition):
        return { 'mForN': (voucherDefinition.lower_bound, voucherDefinition.upper_bound) }


    def update(self, voucherDefinition, inData):

        # So I don't mess up data
        data = {}
        data.update(inData)

        data.update(boundsFromFormFields(data['mForN']))
        data.pop('mForN')

        commonValidation(data)

        voucherDefinition.categories = data['categories']
        voucherDefinition.start_date = data['start_date']
        voucherDefinition.end_date = data['end_date']
        voucherDefinition.amount = data['amount']
        voucherDefinition.lower_bound = data['lower_bound']
        voucherDefinition.upper_bound = data['upper_bound']




