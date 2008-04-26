from twisted.internet import defer
from nevow import inevow, loaders, url
from poop.objstore import NotFound
import formal

from tub.web import page, util, categorieswidget

from cms import contenttypeutil

from pollen.nevow.tabular import tabular, cellrenderers

from ecommerce.customer import public_utils


def loader(filename):
    return loaders.xmlfile(util.resource_filename('ecommerce.customer.templates',
        filename), ignoreDocType=True)


def mapData(form, data, fromKeyFunc, toKeyFunc):
    """Map product data to and from formal data keys"""
    rv = {}

    def visitItem(item):
        fromName = fromKeyFunc(item)
        toName = toKeyFunc(item)

        value = data[fromName]
        rv[toName] = value

    def visit(node):
        if hasattr(node, 'items'):
            for item in node.items:
                visit(item)
        else:
            visitItem(node)

    visit(form)
    return rv

def getDataFromForm(form, data):
    return mapData(form, data, 
        lambda item: item.key,
        lambda item: item.key.rsplit('.', 1)[-1] )
    

def putDataToForm(form, data):

    form.data = mapData(form, data, 
        lambda item: item.key.rsplit('.', 1)[-1],
        lambda item: item.key)


def addCustomerFields(form, customer=None, billingCountryOptions=None):
    """
    Add customer fields to a form.

    """

    public_utils.addCoreFields(form, False, billingCountryOptions=billingCountryOptions)


    if customer:
        data = dict((attr,getattr(customer,attr,None)) for attr in customer._attrs)
        putDataToForm(form, data) 

        crmData = formal.Group('crmData')
        form.add( crmData )
        for key, value in customer.crmData.iteritems():
            crmData.add( formal.Field( key, formal.String(immutable=True)) )
            form.data['crmData.%s'%key] = value


class EditCustomerPage(formal.ResourceMixin, page.Page):

    componentContent = loader('EditCustomer.html')

    def __init__(self, original, application):
        super(EditCustomerPage, self).__init__(original)
        self.application = application

    def form_customer(self, ctx):

        def buildForm(billingCountryOptions):
            form = formal.Form()
            addCustomerFields(form, self.original, billingCountryOptions)
            form.addAction(self._submit, label='Update Customer Details' )
            return form

        if self.application.billingCountryFileName:
            d = defer.succeed(public_utils.getBillingCountryOptions(self.application.billingCountryFileName))
        else:
            d = defer.succeed(None)
        d.addCallback(buildForm)
        return d

    def _submit(self, ctx, form, data):
        sess = util.getStoreSession(ctx)

        def updated(customer):
            return url.URL.fromContext(ctx).replace('message', 'Customer updated successfully')

        def updateFailed(failure):
            failure.trap(NotFound)
            util.getStoreSession(ctx).forceRollback = True
            return url.URL.fromContext(ctx).replace('errormessage', 'Customer update failed. Someone else has already changed the customer.')

        def update(ignore):
            for attr in ('email', 'last_name', 'first_name', 'phoneNumber', 
                'billingAddress1', 'billingAddress2', 'billingAddress3', 
                'billingCity', 'billingPostcode', 'billingCountry', 'optIn',
                'gender', 'dateOfBirth', 'secretQuestion', 'secretAnswer'):
                value = data[attr]
                setattr(self.original, attr, value)

            if data['password']:
                self.original.password = data['password']

            d = self.application.getManager()
            d.addCallback(lambda manager: manager.update(self.original, sess) )
            return d

        data = getDataFromForm(form, data)

        d = defer.Deferred()
        d.addCallback(lambda ignore: update(data))
        d.addCallback(lambda ignore: sess.flush())
        d.addCallback(updated)
        d.addErrback(updateFailed)
        d.callback(None)
        return d

class CustomerTabularView(tabular.TabularView):
    docFactory = loader('CustomerTabularView.html')

class CustomerPage(formal.ResourceMixin, page.Page):
    """Page used for listing customer and navigating to customer instance editor. Also
    used to create and delete customer.
    """
    componentContent = loader('Customers.html')

    def __init__(self, application):
        super(CustomerPage, self).__init__()
        self.application = application

    def child__submitDelete(self, ctx):
        sess = util.getStoreSession(ctx)

        # Get the list of customer ids to delete from the form and
        ids = inevow.IRequest(ctx).args.get('id')
        if not ids:
            return url.URL.fromContext(ctx)

        def removeCustomer(manager, id):
            d = manager.remove(sess, id)
            d.addCallback(lambda ignore: manager)
            return d

        def customersDeleted(spam):
            return url.URL.fromContext(ctx).replace('message', 'Customers deleted successfully')

        d = self.application.getManager()
        for id in ids:
            d.addCallback(removeCustomer, id)
        d.addCallback(lambda spam: sess.flush())
        d.addCallback(customersDeleted)
        return d

#    def render_customer_table_form(self, ctx, customer):
#        return ctx.tag(action=url.here.child('_submitDelete'))

    def childFactory(self, ctx, id):
        # IDs are always ints
        try:
            id = int(id)
        except ValueError:
            return None

        def error(failure):
            failure.trap(NotFound)
            return None

        sess = util.getStoreSession(ctx)
        d = self.application.getManager()
        d.addCallback(lambda manager: manager.findById(sess, id))
        return d.addCallback(EditCustomerPage, self.application).addErrback(error)

#    def render_newCustomer(self, ctx, data):
#        return ctx.tag(href=url.here.child('new'))

#    def child_new(self, ctx):
#        return NewCustomerPage(self.application)

    def form_search(self, ctx):

        form = formal.Form()
        form.data = {}
        form.addField('last_name', formal.String(),
            description="Enter the last name of a customer or partial last name with wildcard '*'", label="Last Name")
        form.addField('first_name', formal.String(),
            description="Enter the first name of a customer or partial first name with wildcard '*'", label="First Name")
        form.addField('email', formal.String(),
            description="Enter the email address of a customer or partial email address with wildcard '*'")

        form.addAction(self._search, label='Search')

        form.data = self._getSearchCriteria(ctx)

        return form

    def _search(self, ctx, form, data):

        u = url.URL.fromContext(ctx)

        for column in ('last_name', 'first_name', 'email'):
            value = data[column]
            if value:
                u = u.replace(column, value)
            else:
                u = u.remove(column)

        return u

    def _getSearchCriteria(self, ctx):
        rv = {}
        rv['last_name'] = inevow.IRequest(ctx).args.get('last_name', [None])[0]
        rv['first_name'] = inevow.IRequest(ctx).args.get('first_name', [None])[0]
        rv['email'] = inevow.IRequest(ctx).args.get('email', [None])[0]
        
        return rv

    def render_customer_table(self, ctx, data):
        def gotModel(model):
            model.attributes['id'] = tabular.Attribute(sortable=False)
            model.attributes['name'] = tabular.Attribute(sortable=True)
            model.attributes['email'] = tabular.Attribute(sortable=True)

            view = CustomerTabularView('customers', model, 20)
#            view.columns.append(tabular.Column('id', '', 
#                cellrenderers.CheckboxRenderer('id')))
            view.columns.append(tabular.Column('name', 'Name', 
                cellrenderers.LinkRenderer(url.URL.fromContext(ctx), 'id' )))
            view.columns.append(tabular.Column('email', 'Email'))

            return view

        storeSession = util.getStoreSession(ctx)
        d = self.application.getManager()
        d.addCallback(lambda manager: 
            manager.getTabularModel(storeSession, self._getSearchCriteria(ctx)))
        d.addCallback(gotModel)
        return d

