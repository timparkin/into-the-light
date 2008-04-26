def crudSQLFactory(table, pkColumns, otherColumns, *accessQueryColumns):
    """Build typical SQL queries for accessing and manipulating a table.
    
    By default SQL for creating, reading all records, reading a single record
    (identified by the primary key), updating and deleting (by primary key) is
    returned.
    
    Additional SELECT queries can be built by specifying additional column sets
    as accessQueryColumns.
    
    Parameters:
        table:
            name of the table
        pkColumns:
            sequence of primary key columns
        otherColumns:
            sequence of other (non primary key) columns
        accessQueryColumns:
            Optional sequence of sequences of columns.
            
    Returns a tuple of SQL statements.
    
    There following are always returned:
        
        * create
        * read all
        * read one (by primary key)
        * update
        * delete (by primary key)
        
    An additional SQL query is returned for each of the accessQueryColumns. The
    SQL is equivalent to that of read one but the where clause uses the access
    columns instead of the primary key columns.
    
    Examples:
        
        >>> create, readAll, readOne, update, delete = \
            crudSQLFactory('person', ['id'], ['name', 'email', 'password'])
            
        Creates standard SQL for managing a person table with a primary key
        called 'id' and 'name', 'email' and 'password' columns.
        
        >>> create, readAll, readOne, update, delete, readByEmail, readByEmailAndPassword = \
            crudSQLFactory('person', ['id'], ['name', 'email', 'password'], ['email'], ['email', 'password'])
            
        Creates standard SQL for managing a person table (as above) but also
        creates SQL for querying the person table by email and by email & password.
    """
    
    # pkColumns cannot be empty
    if not pkColumns:
        raise ValueError('pkColumns cannot be empty')
    
    # otherColumns cannot be empty or we cannot build a update SQL.
    if not otherColumns:
        raise ValueError('otherColumns cannot be empty')
        
    # Utility functions
    commaSep = lambda cols: ', '.join(cols)
    commaSepParam = lambda cols: ', '.join(['%%(%s)s'%col for col in cols])
    commaSepEqParam = lambda cols: ', '.join(['%s=%%(%s)s'%(col,col) for col in cols])
    andSepEqParam = lambda cols: ' and '.join(['%s=%%(%s)s'%(col,col) for col in cols])
    selectWhereSQL = lambda table, cols, whereCols: "select %s from %s where %s" % (commaSep(cols), table, andSepEqParam(whereCols))
    
    # Build a list of all the columns in the table
    allColumns = pkColumns + otherColumns
    
    # Build the common queries
    createSQL = "insert into %s (%s) values (%s)" % (table, commaSep(allColumns), commaSepParam(allColumns))
    readAllSQL = "select %s from %s" % (commaSep(allColumns), table) 
    readOneSQL = selectWhereSQL(table, allColumns, pkColumns)
    updateSQL = "update %s set %s where %s" % (table, commaSepEqParam(otherColumns), andSepEqParam(pkColumns))
    deleteSQL = "delete from %s where %s" % (table, andSepEqParam(pkColumns))
    
    # Build the access queries
    accessSQLs = [selectWhereSQL(table, allColumns, cols) for cols in accessQueryColumns]
    
    # Return all the SQL statements
    return [createSQL, readAllSQL, readOneSQL, updateSQL, deleteSQL] + accessSQLs
    
    
if __name__ == '__main__':
    import unittest
    
    class TestCRUD(unittest.TestCase):
        
        def test_noPkColumns(self):
            self.assertRaises(ValueError, crudSQLFactory, 'table', [], ['foo'])
        
        def test_noOtherColumns(self):
            self.assertRaises(ValueError, crudSQLFactory, 'table', ['id'], [])
        
        def test_createSQL(self):
            sql = crudSQLFactory('table', ['id'], ['foo'])[0]
            self.failUnless(sql == "insert into table (id, foo) values (%(id)s, %(foo)s)")
            sql = crudSQLFactory('table', ['id'], ['foo', 'bar'])[0]
            self.failUnless(sql == "insert into table (id, foo, bar) values (%(id)s, %(foo)s, %(bar)s)")
            
        def test_readAllSQL(self):
            sql = crudSQLFactory('table', ['id'], ['foo'])[1]
            self.failUnless(sql == "select id, foo from table")
            sql = crudSQLFactory('table', ['id'], ['foo', 'bar'])[1]
            self.failUnless(sql == "select id, foo, bar from table")
        
        def test_readOneSQL(self):
            sql = crudSQLFactory('table', ['id'], ['foo'])[2]
            self.failUnless(sql == "select id, foo from table where id=%(id)s")
            sql = crudSQLFactory('table', ['id'], ['foo', 'bar'])[2]
            self.failUnless(sql == "select id, foo, bar from table where id=%(id)s")
            
        def test_updateSQL(self):
            sql = crudSQLFactory('table', ['id'], ['foo'])[3]
            self.failUnless(sql == "update table set foo=%(foo)s where id=%(id)s")
            sql = crudSQLFactory('table', ['id'], ['foo', 'bar'])[3]
            self.failUnless(sql == "update table set foo=%(foo)s, bar=%(bar)s where id=%(id)s")
            
        def test_deleteSQL(self):
            sql = crudSQLFactory('table', ['id'], ['foo', 'bar'])[4]
            self.failUnless(sql == "delete from table where id=%(id)s")
            
        def test_multiplePkCols(self):
            sqls = crudSQLFactory('table', ['id1', 'id2'], ['foo'])
            self.failUnless(sqls[0] == "insert into table (id1, id2, foo) values (%(id1)s, %(id2)s, %(foo)s)")
            self.failUnless(sqls[1] == "select id1, id2, foo from table")
            self.failUnless(sqls[2] == "select id1, id2, foo from table where id1=%(id1)s and id2=%(id2)s")
            self.failUnless(sqls[3] == "update table set foo=%(foo)s where id1=%(id1)s and id2=%(id2)s")
            self.failUnless(sqls[4] == "delete from table where id1=%(id1)s and id2=%(id2)s")
        
        def test_accessSQL(self):
            sqls = crudSQLFactory('table', ['id'], ['foo', 'bar'], ['foo'], ['bar'], ['foo', 'bar'])
            self.failUnless(sqls[5] == "select id, foo, bar from table where foo=%(foo)s")
            self.failUnless(sqls[6] == "select id, foo, bar from table where bar=%(bar)s")
            self.failUnless(sqls[7] == "select id, foo, bar from table where foo=%(foo)s and bar=%(bar)s")
        
    unittest.main()
    
