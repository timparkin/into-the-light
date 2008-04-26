import os.path

from zope.interface import implements
from twisted.internet import defer
from twisted.python import log

from nevow import inevow, loaders, url
from tub.web import page, util
from pollen.nevow.tabular import cellrenderers, itabular, tabular

import formal

from ecommerce.voucher import manager


def loader(filename):
    return loaders.xmlfile(util.resource_filename('ecommerce.voucher',
        os.path.join('templates',filename)), ignoreDocType=True)



class VoucherDefinitionsPage(formal.ResourceMixin, page.Page):
    """
    List the voucher definitions in the system.
    """

    componentContent = loader('VoucherDefinitionsPage.html')

    def __init__(self, avatar, app, voucherType):
        super(VoucherDefinitionsPage, self).__init__()
        self.avatar = avatar
        self.app = app
        self.voucherType = voucherType


    def data_voucher_definitions(self, ctx, data):
  
        storeSession = util.getStoreSession(ctx)
        def voucherDefinitionFactory():
            return self.app.getManager().getVoucherDefinitions(storeSession)

        return VoucherDefinitionsModel(voucherDefinitionFactory)


    def render_voucher_definitions(self, ctx, model):
        """
        Create a tabular view of the sales.
        """
        # Create a link renderer to click to the Voucher Definition instance.
        linkRenderer = cellrenderers.LinkRenderer(url.here, 'voucher_definition_id')

        # Create the view
        view = tabular.TabularView('voucherdefinitions', model, 20)
        view.columns.append(tabular.Column('voucher_definition_id', '',
                cellrenderers.CheckboxRenderer('voucher_definition_id')))
        view.columns.append(tabular.Column('code', 'Code', linkRenderer))
        return view


    def childFactory(self, ctx, name):
        """
        Create a resource for the Voucher Definition instance.
        """

        # A sale is always identified by an int
        try:
            id = int(name)
        except ValueError:
            return

        # Find the sale.
        storeSession = util.getStoreSession(ctx)
        d = self.app.getManager().getVoucherDefinition(storeSession, id)
        # Create the resource to edit the sale
        d.addCallback(lambda voucherDefinition: EditVoucherDefinitionPage(self.avatar, 
            self.app, voucherDefinition, self.voucherType))
        return d


    def render_new(self, ctx, data):
        return ctx.tag(href=url.here.child('new'))


    def child_new(self, ctx):
        return NewVoucherDefinitionPage(self.avatar, self.app, self.voucherType)


    def child__delete(self, ctx):
        storeSession = util.getStoreSession(ctx)

        # Get the list of product ids to delete from the form and
        ids = inevow.IRequest(ctx).args.get('voucher_definition_id')
        if not ids:
            return url.URL.fromContext(ctx)

        def removeVoucherDefinition(manager, id):
            d = manager.delete(storeSession, id)
            d.addCallback(lambda ignore: manager)
            return d

        def vouchersDeleted(spam):
            return url.URL.fromContext(ctx).replace('message', 'Vouchers deleted successfully')

        manager = self.app.getManager()
        d = defer.succeed(manager) 
        for id in ids:
            d.addCallback(removeVoucherDefinition, id)
        d.addCallback(lambda ignore: storeSession.flush())
        d.addCallback(vouchersDeleted)
        return d


    def render_voucher_table_form(self, ctx, data):
        return ctx.tag(action=url.here.child('_delete'))



class NewVoucherDefinitionPage(formal.ResourceMixin, page.Page):

    componentContent = loader('NewVoucherDefinitionPage.html')

    def __init__(self, avatar, app, voucherType):
        super(NewVoucherDefinitionPage, self).__init__()
        self.avatar = avatar
        self.app = app
        self.voucherType = voucherType


    def form_voucher(self, ctx):

        creator = self.voucherType.getCreator()

        form = formal.Form()
        creator.addFields(form)
        form.addAction(self._create)
        return form


    def _create(self, ctx, form, data):
        creator = self.voucherType.getCreator()

        voucherDefinition = creator.create(ctx, form, data)

        def created(voucher):
            return url.URL.fromContext(ctx).sibling(voucher.voucher_definition_id).replace('message', 'Voucher added successfully')

        storeSession = util.getStoreSession(ctx)
        d = self.app.getManager().add(storeSession, voucherDefinition)
        d.addCallback(created)
        return d





class EditVoucherDefinitionPage(formal.ResourceMixin, page.Page):
    """
    Display and edit a voucher definition
    """

    componentContent = loader('EditVoucherDefinitionPage.html')

    def __init__(self, avatar, app, voucherDefinition, voucherType):
        super(EditVoucherDefinitionPage, self).__init__()
        self.avatar = avatar
        self.app = app
        self.voucherDefinition = voucherDefinition
        self.voucherType = voucherType


    def form_voucher_definition(self, ctx):
        form = formal.Form()
        self.voucherType.getEditor().addFieldsAndData(form, self.voucherDefinition)
        form.addAction(self._update)
        return form


    def _update(self, ctx, form, data):

        def updated():
            return url.URL.fromContext(ctx).sibling(self.voucherDefinition.voucher_definition_id).replace('message', 'Voucher updated successfully')

        self.voucherType.getEditor().update(self.voucherDefinition, data)
        
        storeSession = util.getStoreSession(ctx)
        d = self.app.getManager().update(storeSession, self.voucherDefinition)
        d.addCallback(lambda ignore: updated())
        return d


    def data_vouchers(self, ctx, data):
        return VoucherModel(self.voucherDefinition.vouchers)


    def render_vouchers(self, ctx, model):
        # Create the view
        view = tabular.TabularView('vouchers', model, 20)
        view.columns.append(tabular.Column('code', 'Code'))
        view.columns.append(tabular.Column('used', 'Used', DefaultCellRenderer()))
        return view



class DefaultCellRenderer(object):
    implements(itabular.ICellRenderer)


    def rend(self, patterns, item, attribute):

        dataCell = patterns.patternGenerator('dataCell')
        cellTag = dataCell()
        cellTag.fillSlots('value',
                item.getAttributeValue(attribute) or '')
        return cellTag



class VoucherDefinitionsModel(object):

    implements(itabular.IModel)

    attributes = {
        'voucher_definition_id': tabular.Attribute(),
        'code': tabular.Attribute(),
        }


    def __init__(self, factory):
        self.factory = factory
        self._cache = None


    def setOrder(self, attribute, direction):
        raise NotImplemented()


    def getItemCount(self):
        d = self._getVoucherDefinitions()
        d.addCallback(lambda voucherDefinitions: len(voucherDefinitions))
        return d


    def getItems(self, start, end):
        d = self._getVoucherDefinitions()
        d.addCallback(lambda voucherDefinitions: voucherDefinitions[start:end])
        return d


    def _getVoucherDefinitions(self):
        if self._cache is not None:
            return defer.succeed(self._cache)
        def voucherDefinitionToDict(voucherDefinition):

            data = {
                'voucher_definition_id': voucherDefinition.voucher_definition_id,
                'code': voucherDefinition.code,
                }
            return data
        def cacheAndReturn(voucherDefinitions):
            self._cache = map(voucherDefinitionToDict, voucherDefinitions)
            return self._cache

        d = self.factory()
        d.addCallback(cacheAndReturn)
        return d



class VoucherModel(object):

    implements(itabular.IModel)

    attributes = {
        'voucher_id': tabular.Attribute(),
        'code': tabular.Attribute(),
        'used': tabular.Attribute(),
        'sales_order': tabular.Attribute(),
        }


    def __init__(self, data):
        self.data = [ voucher.getDataDict() for voucher in data ]


    def setOrder(self, attribute, direction):
        raise NotImplemented()


    def getItemCount(self):
        d = defer.succeed(len(self.data))
        return d


    def getItems(self, start, end):
        d = defer.succeed(self.data[start:end])
        return d



