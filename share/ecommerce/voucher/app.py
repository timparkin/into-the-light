from zope.interface import implements
from twisted.internet import defer

from tub import itub
from ecommerce.voucher import web, manager, basic, categorised

BASIC_VOUCHER = 'basic'
CATEGORISED_VOUCHER = 'categorised'

voucher_types =  {
    BASIC_VOUCHER: basic.Voucher(),
    CATEGORISED_VOUCHER: categorised.Voucher(),
}


class VoucherApplication(object):
    implements(itub.IApplication)

    name = "voucher"
    version = 1
    label = "Voucher Management"
    description = "Voucher Management"


    def __init__(self, type=None):
        if type is None:
            type = BASIC_VOUCHER

        self.voucherType = voucher_types[type]


    def setParent(self, parent):
        self.parent = parent


    def initialize(self, realm):
        pass


    def getComponents(self):
        return [VoucherDefinitionComponent(self, self.voucherType)]


    def getManager(self):
        return manager.VoucherManager(self.voucherType)


    def getServices(self):
        return self.parent.services


    services = property(getServices)



class VoucherDefinitionComponent(object):
    implements(itub.IApplicationComponent)

    name = "voucher"
    label = "Voucher Management"
    description = "Voucher Management"


    def __init__(self, application, voucherType):
        super(VoucherDefinitionComponent, self).__init__()
        self.application = application
        self.voucherType = voucherType


    def resourceFactory(self, avatar, storeSession, segments):
        return web.VoucherDefinitionsPage(avatar, self.application, self.voucherType), segments

