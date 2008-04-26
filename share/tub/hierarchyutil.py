def isUniquePath(curs, table, column, path, newChild):
    """
    Ensure that a child of a path is unique amongst its siblings.
    """
    path = '.'.join( (path, newChild) )
    sql = 'select count( 1 ) from %s where %s = %%s' % (table, column)

    def _( r ):
        if r[0] > 0:
            return False
        return True

    d = curs.execute( sql, (path,) )
    d.addCallback(lambda ignore: curs.fetchone())
    d.addCallback( _ )
    return d
