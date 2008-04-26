from twisted.internet import defer

class IStock(object):


    def getCurrentLevel(storeSession, product_id):
        """Returns current stock level of the product"""
        pass


    def adjustLevel(storeSession, product_id, adjustment):
        """Adjusts the current level of stock of the product and
           returns new stock level of the product"""
        pass


    def getCurrentLevels(storeSession, product_ids):
        """Takes a sequence of products ids and returns
           a product id to option_code/stock level dictionary"""
        pass


    def tidyStock(storeSession, product_id, option_codes):
        """Remove any records not required"""
        pass



class StockException(Exception):
    pass



class BasicStockManager(object):

    def getCurrentLevel(self, storeSession, product_id, option_code=None):
        sql = """
            select in_stock from basic_stock where product_id = %(product_id)s
        """
        if option_code:
            sql = sql + """ and option_code=%(option_code)s """ 

        def gotLevel(rows):

            if len(rows) == 0:
                d = self._createRecord(storeSession, product_id, option_code)
                d.addCallback(lambda ignore: 0)
                return d
            elif len(rows) > 1:
                raise StockException('Multiple stock records for product %s'%product_id)
            else:
                return rows[0][0]
            
        params = {'product_id': product_id, 'option_code': option_code }
        d = storeSession.curs.execute(sql, params)
        d.addCallback(lambda ignore: storeSession.curs.fetchall())
        d.addCallback(gotLevel)

        return d


    def _createRecord(self, storeSession, product_id, option_code):
        sql = """
            insert into basic_stock (product_id, option_code, in_stock) values (%(product_id)s, %(option_code)s, 0)
        """
        if option_code is None:
            option_code = '' # Need a none null value for the primary key in the database
        d = storeSession.curs.execute( sql, {'product_id': product_id, 'option_code': option_code } )
        return d


    def adjustLevel(self, storeSession, product_id, adjustment, option_code=None):
        sql = """
            update basic_stock set in_stock = in_stock + %(adjustment)s where product_id = %(product_id)s
        """
        if option_code:
            sql = sql + """ and option_code=%(option_code)s """ 

        d = storeSession.curs.execute(sql, {'product_id': product_id, 'adjustment': adjustment, 'option_code': option_code})
        d.addCallback(lambda ignore: self.getCurrentLevel(storeSession, product_id, option_code))
        return d


    def safeAdjustLevel(self, storeSession, product_id, adjustment, option_code=None):
        sql = """
            update basic_stock set in_stock = (in_stock + %(adjustment)s)
            where product_id = %(product_id)s
            and (in_stock + %(adjustment)s) >= 0
        """
        if option_code:
            sql = sql + """ and option_code=%(option_code)s """ 

        def checkUpdate():
            return storeSession.curs.rowcount == 1

        d = storeSession.curs.execute(sql, {'product_id': product_id, 'adjustment': adjustment, 'option_code': option_code})
        d.addCallback(lambda ignore: checkUpdate())
        return d


    def getCurrentLevels(self, storeSession, product_ids):
        sql = """
            select product_id, option_code, in_stock from basic_stock where product_id in (%(id_list)s)
        """

        def gotLevels(rows):
            rv = dict( [(int(id),[]) for id in product_ids] )

            for row in rows:
                key = int(row[0])
                option_code = row[1]
                if option_code == '':
                    option_code = None
                level = row[2]
                rv[key].append( {'option_code':option_code, 'level':level} )

            # Add empty records
            for id in rv.keys():
                if rv[id] == []:
                    rv[id]. append( {'option_code':None, 'level':0} )

            return rv

        params = {}
        id_list = []
        for id in product_ids:
            key = 'id_%s'%id
            id_list.append('%%(%s)s'%key)
            params[key] = id

        id_list = ", ".join(id_list)
        d = storeSession.curs.execute(sql%{'id_list': id_list}, params)
        d.addCallback(lambda ignore: storeSession.curs.fetchall())
        d.addCallback(gotLevels)
        return d


    def tidyStock(self, storeSession, product_id, option_codes):

        noOptionsSQL = """
            delete from basic_stock where product_id = %(product_id)s and option_code != ''
        """
        # Products without options have '' (not NULL) in their option code column.

        optionsSQL = """
            delete from basic_stock where product_id = %%(product_id)s and option_code not in (%(option_codes)s)
        """

        if option_codes == []:
            d = storeSession.curs.execute(noOptionsSQL, {'product_id': product_id})
        else:
            codes = []
            params = {}
            for i in range(len(option_codes)):
                key = 'code_%s'%i
                params[key] = option_codes[i]
                codes.append( "%%(%s)s"%key )
            codes = ', '.join(codes)
            params['product_id'] = product_id
            sql = optionsSQL%{'option_codes': codes}
            d = storeSession.curs.execute(sql, params)

        return d
