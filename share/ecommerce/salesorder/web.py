import os.path
import datetime
from email.MIMEText import MIMEText

from pollen.mail import mailutil

from zope.interface import implements
from twisted.internet import defer
from twisted.python import log
from twisted.mail import smtp
from twisted.mail.smtp import SMTPDeliveryError

from nevow import flat, accessors, inevow, loaders, url, tags as T
from tub.web import page, util, xforms
from pollen.nevow.tabular import cellrenderers, itabular, tabular

from ecommerce.salesorder import manager

STATUS_OPTIONS = [manager.SalesOrder.CONFIRMED, manager.SalesOrder.PROCESSED, manager.SalesOrder.CANCELLED, manager.SalesOrder.PENDING]
STATUS_OPTIONS = zip(STATUS_OPTIONS, STATUS_OPTIONS)


def loader(filename):
    return loaders.xmlfile(util.resource_filename('ecommerce.salesorder',
        os.path.join('templates',filename)), ignoreDocType=True)



class SalesOrdersPage(xforms.ResourceMixin, page.Page):
    """
    List the sales in the system.
    """

    componentContent = loader('SalesOrdersPage.html')

    def __init__(self, avatar, app):
        super(SalesOrdersPage, self).__init__()
        self.avatar = avatar
        self.app = app


    def data_salesorders(self, ctx, data):
        """
        Build a sales model for the view.
        """
        # Get the status, default to confirmed
        status = ctx.arg('status') or manager.SalesOrder.CONFIRMED
        storeSession = util.getStoreSession(ctx)

        def salesOrdersFactory():
            def _(**kw):
                return self.app.getManager().getSalesOrders(storeSession, **kw)
            return _

        return SalesOrdersModel(salesOrdersFactory(), status=status)


    def form_view(self, ctx):

        def changeView(ctx, form, data):
            return url.here.replace('status', data['status'])

        form = xforms.Form()
        form.addField('status', xforms.String(required=True),
                xforms.widgetFactory(xforms.SelectChoice,
                    options=STATUS_OPTIONS, noneOption=None))
        form.addAction(changeView)
        form.data = {'status': ctx.arg('status')}
        return form


    def render_salesorders(self, ctx, model):
        """
        Create a tabular view of the sales.
        """
        # Create a link renderer to click to the Sale instance.
        linkRenderer = cellrenderers.LinkRenderer(url.here, 'sales_order_id')
        # Create the view
        view = tabular.TabularView('salesorders', model, 20)
        view.columns.append(tabular.Column('order_num', 'Order Number', linkRenderer))
        view.columns.append(tabular.Column('name', 'Name'))
        view.columns.append(tabular.Column('total', 'Total'))
        view.columns.append(tabular.Column('date', 'Date'))
        view.columns.append(tabular.Column('processed_date', 'Processed'))
        return view


    def childFactory(self, ctx, name):
        """
        Create a resource for the Sale instance.
        """

        # A sale is always identified by an int
        try:
            salesOrderId = int(name)
        except ValueError:
            return

        # Find the sale.
        storeSession = util.getStoreSession(ctx)
        d = self.app.getManager().getSalesOrder(storeSession, salesOrderId)
        # Create the resource to edit the sale
        d.addCallback(lambda salesOrder: SalesOrderPage(self.avatar, self.app, salesOrder))
        return d



class SalesOrderPage(xforms.ResourceMixin, page.Page):
    """
    Display and edit a sale instance.
    """

    componentContent = loader('SalesOrderPage.html')

    def __init__(self, avatar, app, salesOrder):
        super(SalesOrderPage, self).__init__()
        self.avatar = avatar
        self.app = app
        self.salesOrder = salesOrder


    def data_salesorder(self, ctx, data):
        return accessors.ObjectContainer(self.salesOrder)


    def render_address(self, ctx, data):
        tag = ctx.tag.clear()
        if data is None:
            return tag[ '-' ]
        else:
            return tag[ [(l,T.br()) for l in data.splitlines()] ]


    def render_basket_item(self, ctx, basketItem):
        ctx.tag.fillSlots('code', basketItem.code or '')
        ctx.tag.fillSlots('description', T.xml(basketItem.description) or '')
        ctx.tag.fillSlots('quantity_ordered', basketItem.quantity_ordered)
        ctx.tag.fillSlots('unit_price', basketItem.unit_price)
        ctx.tag.fillSlots('total_price', basketItem.total_price)
        return ctx.tag


    def form_actions(self, ctx):
        form = xforms.Form()
        if self.salesOrder.payment_reference and self.salesOrder.status == manager.SalesOrder.CONFIRMED:
            form.addAction(self.processed, 'processed')
        if self.salesOrder.status in (manager.SalesOrder.CONFIRMED, manager.SalesOrder.PENDING):
            form.addAction(self.cancelled, 'cancelled')
        return form


    def processed(self, ctx, form, data):
        storeSession = util.getStoreSession(ctx)
        d = self.app.getManager().markAsProcessed(storeSession, self.salesOrder)
        d.addCallback(self._sendSalesOrderProcessedEmail, ctx)
        d.addCallback(lambda ignore: url.here.up())
        return d


    def cancelled(self, ctx, form, data):
        storeSession = util.getStoreSession(ctx)
        d = self.app.getManager().markAsCancelled(storeSession, self.salesOrder)
        d.addCallback(lambda ignore: url.here.up())
        return d


    def _sendSalesOrderProcessedEmail(self, salesOrder, ctx):


        def getEmailHTML():
            emailPage = SalesOrderProcessedEmail(self.app.config['sales_order']['sales_order_processed_email_template'], salesOrder)
            return emailPage.renderSynchronously()


        def sendEmail(emailHTML):

            fromAddress = self.app.config['mailService']['fromEmail']
            toAddress = [salesOrder.customer_email]
            msg = mailutil.createhtmlmail(fromAddress, toAddress, 'Order Processed', emailHTML)
            return MailService(self.app.config).sendMessage(toAddress, fromAddress, msg)


        if self.app.htmlEmailFactory:
            storeSession = util.getStoreSession(ctx)
            d = self.app.htmlEmailFactory(ctx, self.avatar, storeSession, self.app.config, salesOrder)
        else:
            d = defer.succeed(getEmailHTML())
        d.addCallback(sendEmail)
        return d


    def render_if(self, ctx, data):
        return render_if(ctx, data)


    def render_actions(self, ctx, data):
        if self.salesOrder.status in (manager.SalesOrder.PENDING, manager.SalesOrder.CONFIRMED):
            return ctx.tag
        else:
            return ''



class MailService(object):

    def __init__(self, config):
        self.smtpServer = config['mailService']['smtpServer']


    def _sendmail(self, toAddress, fromAddress, msg):
        d = smtp.sendmail(self.smtpServer, fromAddress, toAddress, msg)
        d.addErrback(self._handleMailError)
        return d


    def _handleMailError(self, failure):
        log.err(failure)
        failure.trap(SMTPDeliveryError)
        raise MailException(str(failure.value))


    def sendMessage(self, toAddress, fromAddress, message):
        return self._sendmail(toAddress, fromAddress, message)



class SalesOrderProcessedEmail(page.Page):

    def __init__(self, template, salesOrder):
        super(SalesOrderProcessedEmail, self).__init__()
        self.docFactory = loaders.xmlfile(template)
        self.salesOrder = salesOrder


    def data_sales_order(self, ctx, data):
        return accessors.ObjectContainer(self.salesOrder)



def render_if(ctx, data):

    # Look for (optional) patterns.
    truePatterns = ctx.tag.allPatterns('True')
    falsePatterns = ctx.tag.allPatterns('False')

    # Render the data. If we found patterns use them, otherwise return the tag
    # or nothing.
    if data:
        if truePatterns:
            return truePatterns
        else:
            return ctx.tag
    else:
        if falsePatterns:
            return falsePatterns
        else:
            return ''



class SalesOrdersModel(object):

    implements(itabular.IModel)

    attributes = {
        'sales_order_id': tabular.Attribute(),
        'order_num': tabular.Attribute(),
        'date': tabular.Attribute(),
        'processed_date': tabular.Attribute(),
        'name': tabular.Attribute(),
        'total': tabular.Attribute(),
        'status': tabular.Attribute(),
        }


    def __init__(self, salesOrdersFactory, status=None, processed_date=None):
        self.salesOrdersFactory = salesOrdersFactory
        self.status = status
        self.processed_date = processed_date
        self._cache = None


    def setOrder(self, attribute, direction):
        raise NotImplemented()


    def getItemCount(self):
        d = self._getSalesOrders()
        d.addCallback(lambda salesOrders: len(salesOrders))
        return d


    def getItems(self, start, end):
        d = self._getSalesOrders()
        d.addCallback(lambda salesOrders: salesOrders[start:end])
        return d


    def _getSalesOrders(self):
        if self._cache is not None:
            return defer.succeed(self._cache)
        def salesOrderToDict(salesOrder):

            data = {
                'sales_order_id': salesOrder.sales_order_id,
                'order_num': salesOrder.order_num,
                'date': salesOrder.create_date.date(),
                'processed_date': (salesOrder.processed_date and salesOrder.processed_date.date()) or '',
                'total': salesOrder.total_price,
                }
            data['name'] = '%s, %s'%(salesOrder.customer_last_name, salesOrder.customer_first_name)

            data['status'] = salesOrder.status
            return data
        def cacheAndReturn(salesOrders):
            self._cache = map(salesOrderToDict, salesOrders)
            return self._cache

        d = self.salesOrdersFactory(status=self.status, processed_date=self.processed_date)
        d.addCallback(cacheAndReturn)
        return d



DATE_FORMAT = '%d/%m/%Y'
TIME_FORMAT = '%H:%M'
DATETIME_FORMAT = DATE_FORMAT + ', ' + TIME_FORMAT


def dateFlattener(date, ctx):
    return date.strftime(DATE_FORMAT)



def timeFlattener(time, ctx):
    return time.strftime(TIME_FORMAT)



def datetimeFlattener(datetime, ctx):
    return datetime.strftime(DATETIME_FORMAT)



flat.registerFlattener(dateFlattener, datetime.date)
flat.registerFlattener(timeFlattener, datetime.time)
flat.registerFlattener(datetimeFlattener, datetime.datetime)

def debug(r, mess):
    print '>>DEBUG', mess, r
    return r
