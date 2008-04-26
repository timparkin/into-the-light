import datetime

from twisted.internet import defer

from pollen import sqlutil

from ecommerce.voucher import base



class VoucherManager(object):

    def __init__(self, voucherType):
        self.voucherType = voucherType
        

        self.voucherDefinitionSQL = sqlutil.crudSQLFactory(
            self.voucherType.getType().__table__, 
            self.voucherType.getType()._attrs[0:1], 
            self.voucherType.getType()._attrs[1:])

        self.voucherSQL = sqlutil.crudSQLFactory(
            base.Voucher.__table__, 
            base.Voucher._attrs[0:1], 
            base.Voucher._attrs[1:])

        voucherDefinitionColumns = ['d.%s'%attr for attr in self.voucherType.getType()._attrs]
        voucherColumns = ['v.%s'%attr for attr in base.Voucher._attrs]
        self.combinedColumns = voucherDefinitionColumns + voucherColumns

        self.combinedSelect = """select %(cols)s 
            from %(voucher_definition_table)s d
            join %(voucher_table)s v on d.voucher_definition_id = v.voucher_definition_id"""% {
                'voucher_definition_table': self.voucherType.getType().__table__,
                'voucher_table': base.Voucher.__table__,
                'cols': ', '.join( self.combinedColumns )}


    def add(self, storeSession, voucherDefinition):

        def _addVoucherDefinition(row):
            voucherDefinition.voucher_definition_id = row[0]
            return storeSession.curs.execute(self.voucherDefinitionSQL[0], voucherDefinition.getDataDict())


        @defer.deferredGenerator
        def _addVouchers(ignore):

            for voucher in voucherDefinition.vouchers:
                voucher.voucher_definition_id = voucherDefinition.voucher_definition_id
                d = self._addVoucher(voucher, storeSession)
                d = defer.waitForDeferred(d)
                yield d
                d.getResult()


        d = storeSession.curs.execute("""select nextval('voucher_definition_id_seq')""")
        d.addCallback(lambda ignore: storeSession.curs.fetchone())
        d.addCallback(_addVoucherDefinition)
        d.addCallback(_addVouchers)
        d.addCallback(lambda ignore: voucherDefinition)
        return d


    def _addVoucher(self, item, storeSession):

        def _addVoucher(row):
            item.voucher_id = row[0]
            return storeSession.curs.execute(self.voucherSQL[0], item.getDataDict())

        d = storeSession.curs.execute("""select nextval('voucher_id_seq')""")
        d.addCallback(lambda ignore: storeSession.curs.fetchone())
        d.addCallback(_addVoucher)
        return d


    def update(self, storeSession, voucherDefinition):
        sql = self.voucherType.getUpdateSQL()
        sql = sql%{'table': self.voucherType.getType().__table__}


        def checkUpdate():
            if storeSession.curs.rowcount != 1:
                raise 'Update failed'


        d = storeSession.curs.execute(sql, voucherDefinition.getDataDict())
        d.addCallback(lambda ignore: checkUpdate())
        return d


    def delete(self, storeSession, voucher_definition_id):
        sql = self.voucherDefinitionSQL[4]

        d = storeSession.curs.execute(sql, {'voucher_definition_id': voucher_definition_id})
        return d
        

    def getVoucherDefinitions(self, storeSession, id=None):

        where = []
        params = {}

        if id:
            where.append( ' d.voucher_definition_id = %(voucher_definition_id)s ' )
            params['voucher_definition_id'] = id

        if where:
            where = ' and '.join(where)
            sql = self.combinedSelect + ' where ' + where
        else:
            where = None
            params = None
            sql = self.combinedSelect
        
        d = storeSession.curs.execute(sql, params)
        d.addCallback(lambda ignore: storeSession.curs.fetchall())
        d.addCallback(self._buildVoucherDefinitionsFromDb)
        return d


    def _buildVoucherDefinitionsFromDb(self, rows):
        rv = []
        currVoucherDefinition = None
        for row in rows:
            data = dict( zip(self.combinedColumns, row) )
            dData = {}
            vData = {}
            for k, value in data.iteritems():
                type, column = k.split('.')
                if type == 'd':
                    dData[column] = value
                else:
                    vData[column] = value

            if currVoucherDefinition is None or currVoucherDefinition.voucher_definition_id != dData['voucher_definition_id']:
                currVoucherDefinition = self.voucherType.getType()(**dData)
                rv.append(currVoucherDefinition)

            currVoucherDefinition.addVoucher( base.Voucher(**vData) )

        return rv
                    

    def getVoucherDefinition(self, storeSession, id):

        def gotVoucherDefinitions(voucherDefinitions):
            if not voucherDefinitions:
                return None
            else:
                return voucherDefinitions[0]

        d = self.getVoucherDefinitions(storeSession, id=id)
        d.addCallback(gotVoucherDefinitions)
        return d


    def getVoucher(self, storeSession, code, checkAvailability = None):
        """Get a voucher by code"""

        def gotVoucherDefinitions(voucherDefinitions):
            if not voucherDefinitions:
                return None

            rv = voucherDefinitions[0]
            if not checkAvailability:
                return rv

            now = datetime.datetime.utcnow().date()
            if rv.start_date and rv.start_date > now:
                return None
            if rv.end_date and rv.end_date < now:
                return None
            if not rv.multiuse and rv.vouchers[0].used is not None:
                return None
            return rv

        where = []
        params = {}

        where.append( ' v.code = %(code)s ' )
        params['code'] = code

        where = ' and '.join(where)
        sql = self.combinedSelect + ' where ' + where
        
        d = storeSession.curs.execute(sql, params)
        d.addCallback(lambda ignore: storeSession.curs.fetchall())
        d.addCallback(self._buildVoucherDefinitionsFromDb)
        d.addCallback(gotVoucherDefinitions)
        return d


    def reserve(self, storeSession, code):


        def checkUpdate():
            return storeSession.curs.rowcount == 1
            

        def updateVoucher(voucher):
            if not voucher:
                return False

            sql = """
                update %(table)s set previous_used=used, used=%%(now)s where voucher_id=%%(voucher_id)s
            """%{'table': base.Voucher.__table__ }

            if voucher.multiuse == False:
                sql = sql + " and used is NULL" 

            d = storeSession.curs.execute(sql, 
                {'now': datetime.datetime.utcnow(), 
                'voucher_id': voucher.vouchers[0].voucher_id } )
            d.addCallback(lambda ignore: checkUpdate())
            return d

            
        d = self.getVoucher(storeSession, code, checkAvailability=True)
        d.addCallback(updateVoucher)
        return d



    def release(self, storeSession, code):
        sql = """
            update %(table)s set used=previous_used where code=%%(code)s
        """%{'table': base.Voucher.__table__ }

        d = storeSession.curs.execute(sql, {'code': code})
        return d



def debug(r, mess):
    print '>>DEBUG', mess, r
    return r


