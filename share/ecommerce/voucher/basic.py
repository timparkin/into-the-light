import re

import formal

from ecommerce.voucher import base


class Voucher(object):

    def getCreator(self):
        return BasicVoucherDefinitionCreator()        


    def getEditor(self):
        return BasicVoucherDefinitionEditor()        


    def getType(self):
        return BasicVoucherDefinition


    def getUpdateSQL(self):
        sql = """
            update %(table)s 
                set start_date=%%(start_date)s, end_date=%%(end_date)s, amount=%%(amount)s
            where
                voucher_definition_id = %%(voucher_definition_id)s"""

        return sql



class BasicVoucherDefinition(base.BaseVoucherDefinition):

    _attrs = (
        'voucher_definition_id',
        'code',
        'count',
        'multiuse',
        'start_date',
        'end_date',
        'amount'
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

    form.add( formal.Field('count', countField) )
    form.add( formal.Field('multiuse', multiuseField) )
    form.add( formal.Field('start_date', formal.Date()) )
    form.add( formal.Field('end_date', formal.Date()) )
    form.add( formal.Field('amount', formal.String(required=True, strip=True), description="Either an amount or a '%'") )

    return form



class BasicVoucherDefinitionCreator(object):


    def addFields(self, form):
        addFields(form, forCreate = True)


    def create(self, ctx, form, data):

        if not data['multiuse'] and not data['count']:
            raise formal.FormError( "One of 'multiuse' and 'count' must be specified" )

        if data['multiuse'] and data['count']:
            raise formal.FormError( "Only one of 'multiuse' and 'count' must be specified" )

        if not AMOUNT_RE.match(data['amount']):
            raise formal.FieldError( "Unrecognised format", 'amount' )

        voucherDefinition = BasicVoucherDefinition(**data)

        if data['multiuse']:
            voucher = base.Voucher(code=data['code'])
            voucherDefinition.addVoucher(voucher)
        else:
            codes = base.generateCodes(data['code'], data['count'])
            for code in codes:
                voucher = base.Voucher(code=code)
                voucherDefinition.addVoucher(voucher)

        return voucherDefinition


class BasicVoucherDefinitionEditor(object):

    def addFieldsAndData(self, form, voucherDefinition):
        addFields(form)
        form.data = voucherDefinition.getDataDict()


    def update(self, voucherDefinition, data):

        if not AMOUNT_RE.match(data['amount']):
            raise formal.FieldError( "Unrecognised format", 'amount' )
        
        voucherDefinition.start_date = data['start_date']
        voucherDefinition.end_date = data['end_date']
        voucherDefinition.amount = data['amount']



