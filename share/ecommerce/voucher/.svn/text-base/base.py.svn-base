import time
import base64
import md5

class BaseVoucherDefinition(object):

    __table__ = "voucher_definition"


    def __init__(self, **kw):

        for attr in self._attrs:
            setattr(self, attr, None)

        for key, value in kw.iteritems():
            if key not in self._attrs:
                raise 'Unexpected keyword %s'%key
            setattr(self, key, value)

        self.vouchers = []


    def getDataDict(self):
        # I'm not sure whether I wat to derived from types.DictType
        # or just provide a dictionary of data. So I'll provide
        # a dictionary of data for the time being

        return dict([ (k,getattr(self, k)) for k in self._attrs ])


    def addVoucher(self, voucher):
        self.vouchers.append(voucher)


def generateCodes(name, requiredNumber):

    codes = set()
    count = 0

    now = time.time()

    while True:
        if len(codes) == requiredNumber:
            return codes
        if count > requiredNumber + 200:
            return codes

        count+=1
        code = base64.b64encode( md5.new(name + str(count) + str(now)).digest(), "00" )[:12]
        code = "%s%s-%s-%s"%(name,code[0:4], code[4:8], code[8:12])
        code = code.upper()
        code = code.strip()
        code = code.replace(' ', '')
        codes.add(code)



class Voucher(object):

    __table__ = "voucher"
    _attrs = (
        'voucher_id',
        'voucher_definition_id',
        'code',
        'used',
        'previous_used',
         )


    def __init__(self, **kw):

        for attr in self._attrs:
            setattr(self, attr, None)

        for key, value in kw.iteritems():
            if key not in self._attrs:
                raise 'Unexpected keyword %s'%key
            setattr(self, key, value)


    def getDataDict(self):
        # I'm not sure whether I wat to derived from types.DictType
        # or just provide a dictionary of data. So I'll provide
        # a dictionary of data for the time being

        return dict([ (k,getattr(self, k)) for k in self._attrs ])
