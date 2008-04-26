from datetime import datetime

from twisted.internet import defer

from pollen import sqlutil


class SalesOrder(object):

    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    CANCELLED = 'CANCELLED'
    PROCESSED = 'PROCESSED'

    __table__ = "sales_order"
    _attrs = (
        'sales_order_id',
        'order_num',
        'status',
        'create_date',
        'processed_date',
        'total_price',
        'customer_id',
        'customer_version',
        'customer_first_name',
        'customer_last_name',
        'customer_address',
        'customer_postcode',
        'customer_country',
        'customer_phone_number',
        'customer_email',
        'payment_reference',
        'delivery_name',
        'delivery_address',
        'delivery_postcode',
        'delivery_country',
        'message' )

    def __init__(self, **kw):

        for attr in self._attrs:
            setattr(self, attr, None)

        self.status = SalesOrder.PENDING
        self.create_date = datetime.utcnow()

        for key, value in kw.iteritems():
            if key not in self._attrs:
                raise 'Unexpected keyword %s'%key
            setattr(self, key, value)

        self.items = []


    def getDataDict(self):
        # I'm not sure whether I wat to derived from types.DictType
        # or just provide a dictionary of data. So I'll provide
        # a dictionary of data for the time being

        return dict([ (k,getattr(self, k)) for k in self._attrs ])


    def addItem(self, salesOrderItem):
        self.items.append(salesOrderItem)



class SalesOrderItem(object):
    __table__ = "sales_order_item"

    _attrs = ( 
        'sales_order_item_id',
        'sales_order_id',
        'code',
        'description',
        'quantity_ordered',
        'quantity_dispatched',
        'unit_price',
        'total_price',
        'item_id',
        'item_version' )

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


class SalesOrderManager(object):

    def __init__(self, config):
        self.config = config

        self.salesOrderSQL = sqlutil.crudSQLFactory(SalesOrder.__table__, SalesOrder._attrs[0:1], SalesOrder._attrs[1:])
        self.salesOrderItemSQL = sqlutil.crudSQLFactory(SalesOrderItem.__table__, SalesOrderItem._attrs[0:1], SalesOrderItem._attrs[1:])

        salesOrderColumns = ['so.%s'%attr for attr in SalesOrder._attrs]
        salesOrderItemColumns = ['soi.%s'%attr for attr in SalesOrderItem._attrs]
        self.combinedColumns = salesOrderColumns + salesOrderItemColumns

        self.combinedSelect = """select %(cols)s 
            from %(sales_order_table)s so
            join %(sales_order_item_table)s soi on soi.sales_order_id = so.sales_order_id"""% {
                'sales_order_table': SalesOrder.__table__,
                'sales_order_item_table': SalesOrderItem.__table__,
                'cols': ', '.join( self.combinedColumns )}

    def add(self, storeSession, salesOrder):

        def _addSalesOrder(row):
            salesOrder.sales_order_id = row[0]
            salesOrderDict = salesOrder.getDataDict()
            salesOrder.order_num = self.config['sales_order']['order_num_pattern']%salesOrderDict
            return storeSession.curs.execute(self.salesOrderSQL[0], salesOrder.getDataDict())


        @defer.deferredGenerator
        def _addSalesOrderItems(ignore):

            for item in salesOrder.items:
                item.sales_order_id = salesOrder.sales_order_id
                d = self._addSalesOrderItem(item, storeSession)
                d = defer.waitForDeferred(d)
                yield d
                d.getResult()

        d = storeSession.curs.execute("""select nextval('sales_order_id_seq')""")
        d.addCallback(lambda ignore: storeSession.curs.fetchone())
        d.addCallback(_addSalesOrder)
        d.addCallback(_addSalesOrderItems)
    
        return d


    def delete(self, storeSession, sales_order_id):
        sql = self.salesOrderSQL[4]

        d = storeSession.curs.execute(sql, {'sales_order_id': sales_order_id})
        return d
        

    def _addSalesOrderItem(self, item, storeSession):

        def _addSalesOrderItem(row):

            item.sales_order_item_id = row[0]
            return storeSession.curs.execute(self.salesOrderItemSQL[0], item.getDataDict())

        d = storeSession.curs.execute("""select nextval('sales_order_item_id_seq')""")
        d.addCallback(lambda ignore: storeSession.curs.fetchone())
        d.addCallback(_addSalesOrderItem)

        return d


    def getSalesOrders(self, storeSession, status=None, processed_date=None, id=None, order_num=None):

        where = []
        params = {}

        if status:
            where.append( ' so.status = %(status)s ' )
            params['status'] = status

        if processed_date:
            where.append( " date_tunc('day', so.processed_date) = date_tunc('day', %(processed_date)s) " )
            params['processed_date'] = processed_date

        if id:
            where.append( ' so.sales_order_id = %(sales_order_id)s ' )
            params['sales_order_id'] = id

        if order_num:
            where.append( ' so.order_num = %(order_num)s ' )
            params['order_num'] = order_num

        if where:
            where = ' and '.join(where)
            sql = self.combinedSelect + ' where ' + where
        else:
            where = None
            params = None
            sql = self.combinedSelect
        
        d = storeSession.curs.execute(sql, params)
        d.addCallback(lambda ignore: storeSession.curs.fetchall())
        d.addCallback(self._buildSalesOrdersFromDb)
        return d


    def _buildSalesOrdersFromDb(self, rows):
        rv = []
        currSalesOrder = None
        for row in rows:
            data = dict( zip(self.combinedColumns, row) )
            soData = {}
            soiData = {}
            for k, value in data.iteritems():
                type, column = k.split('.')
                if type == 'so':
                    soData[column] = value
                else:
                    soiData[column] = value

            if currSalesOrder is None or currSalesOrder.sales_order_id != soData['sales_order_id']:
                currSalesOrder = SalesOrder(**soData)
                rv.append(currSalesOrder)

            currSalesOrder.addItem( SalesOrderItem(**soiData) )

        return rv
                    

    def getSalesOrder(self, storeSession, id):
        def gotSalesOrders(salesOrders):
            if not salesOrders:
                return None
            else:
                return salesOrders[0]
        d = self.getSalesOrders(storeSession, id=id)
        d.addCallback(gotSalesOrders)
        return d


    def markAsProcessed(self, storeSession, salesOrder):
        if salesOrder.processed_date:
            raise Exception("SalesOrder has already been processed.")
        salesOrder.processed_date = datetime.utcnow()
        salesOrder.status = SalesOrder.PROCESSED

        sql = """
            update sales_order set processed_date=%(processed_date)s, status=%(status)s where sales_order_id = %(sales_order_id)s"""

        d = storeSession.curs.execute(sql, salesOrder.getDataDict())
        d.addCallback(lambda ignore: salesOrder)
        return d


    def markAsCancelled(self, storeSession, salesOrder):
        salesOrder.status = SalesOrder.CANCELLED

        sql = """
            update sales_order set status=%(status)s where sales_order_id = %(sales_order_id)s"""

        d = storeSession.curs.execute(sql, salesOrder.getDataDict())
        d.addCallback(lambda ignore: salesOrder)
        return d


    def confirmPurchase(self, storeSession, salesOrder, paymentReference):
        """
        Confirm the purchase and record the transaction ID.
        """
        if salesOrder.status != SalesOrder.PENDING:
            raise Exception("SalesOrder must be PENDING to be confirmed")
        salesOrder.status = SalesOrder.CONFIRMED
        salesOrder.payment_reference = paymentReference

        sql = """
            update sales_order set payment_reference=%(payment_reference)s, status=%(status)s where sales_order_id = %(sales_order_id)s"""

        d = storeSession.curs.execute(sql, salesOrder.getDataDict())
        d.addCallback(lambda ignore: salesOrder)
        return d


def debug(r, mess):
    print '>>DEBUG', mess, r
    return r


