from zope.interface import implements
from twisted.internet import defer
from nevow import loaders, rend, static
import itabular, tabular
import psycopg2


# Demo data
LIST_DATA = [('col1 #%d'%i, 'col2 #%d'%i) for i in xrange(18)]
DICT_DATA = [{'col1':'col1 #%d'%i, 'col2':'col2 #%d'%i} for i in xrange(25)]


conn = psycopg2.connect(database='template1')


class Model(object):
    implements(itabular.IModel)

    sqlCount = "select count(1) from pg_tables"
    sqlRows = """select schemaname, tablename from pg_tables order by "%s" %s
    offset %%(offset)s
    limit %%(limit)s"""

    sortmap = {
        'schema': 'schemaname',
        'table': 'tablename',
    }

    sort = 'schema'
    dir = 'asc'

    def __init__(self):
        self.attributes = {}

    def setOrder(self, name, dir):
        self.sort = name
        self.dir = dir

    def getItemCount(self):
        curs = conn.cursor()
        try:
            curs.execute(self.sqlCount)
            return defer.succeed(curs.fetchone()[0])
        finally:
            curs.close()

    def getItems(self, start, end):
        sql = self.sqlRows % (self.sortmap[self.sort], self.dir.upper())
        curs = conn.cursor()
        try:
            curs.execute(sql, {'offset': start, 'limit': end-start})
            items = [dict(zip(('schema', 'table'), row)) for row in
                    curs.fetchall()]
            return defer.succeed(items)
        finally:
            curs.close()


class Page(rend.Page):
    docFactory = loaders.xmlfile('demo.html')

    child_images = static.File('./images')
    child_styles = static.File('./styles')
    child_scripts = static.File('./scripts')

    def render_listView(self, ctx, data):
        model = tabular.SequenceListModel(LIST_DATA)
        model.attributes[0] = tabular.Attribute()
        model.attributes[1] = tabular.Attribute(sortable=True)
        view = tabular.TabularView('listView', model, 5)
        view.columns.append(tabular.Column(0, 'Col 1'))
        view.columns.append(tabular.Column(1, 'Col 2'))
        return view

    def render_dictView(self, ctx, data):
        model = tabular.SequenceListModel(DICT_DATA)
        model.attributes['col1'] = tabular.Attribute()
        model.attributes['col2'] = tabular.Attribute(sortable=True)
        view = tabular.TabularView('dictView', model, 6)
        view.columns.append(tabular.Column('col1', 'Col 1'))
        view.columns.append(tabular.Column('col2', 'Col 2'))
        return view

    def render_dbView(self, ctx, data):
        model = Model()
        model.attributes['schema'] = tabular.Attribute(sortable=True)
        model.attributes['table'] = tabular.Attribute(sortable=True)
        view = tabular.TabularView('dbView', model, 10)
        view.columns.append(tabular.Column('schema', 'Schema'))
        view.columns.append(tabular.Column('table', 'Table'))
        return view

if __name__ == '__main__':
    import sys
    from twisted.internet import reactor
    from twisted.python import log
    from nevow import appserver
    log.startLogging(sys.stdout)
    site = appserver.NevowSite(Page())
    reactor.listenTCP(8000, site)
    reactor.run()
