import pkg_resources
from zope.interface import implements
from twisted.internet import defer
from twisted.python import components
from nevow import inevow, loaders, rend, tags, url
import cellrenderers, itabular


# Query parameter names
PAGE = 'page'
SORT = 'sort'
DIR = 'dir'


# Sort query parameter values
ASC = 'asc'
DESC = 'desc'


class TabularView(rend.Fragment):
    implements(itabular.ITabularView)
    docFactory = loaders.xmlfile(pkg_resources.resource_filename('pollen.nevow.tabular',
        'TabularView.html'))

    name = None
    itemsPerPage = None

    _patterns = None
    _page = 1

    def __init__(self, name, model, itemsPerPage):
        super(TabularView, self).__init__()
        self.name = name
        self.model = itabular.IModel(model)
        if itemsPerPage is not None:
            self.itemsPerPage = itemsPerPage
        self.columns = []

    def appendColumn(self, column):
        self.columns.append(column)

    def rend(self, ctx, data):
        # Parse the request
        self._parseRequest(inevow.IRequest(ctx))
        # Create the pattern looker upper now
        self._patterns = inevow.IQ(self.docFactory)
        # Get the item count
        d = defer.maybeDeferred(self.model.getItemCount)
        d.addCallback(self._gotCount, ctx, data)
        return d

    def _parseRequest(self, request):
        try:
            self.page = int(self._requestArg(request, PAGE, 1))
        except ValueError:
            self.page = 1
        self.sort = self._requestArg(request, SORT, None)
        self.dir = self._requestArg(request, DIR, ASC)
        if self.sort is not None:
            self.model.setOrder(self.sort, self.dir)

    def _requestArgName(self, arg):
        if self.name is not None:
            arg = '%s-%s' % (self.name, arg)
        return arg

    def _requestArg(self, request, arg, default=None):
        arg = self._requestArgName(arg)
        value = request.args.get(arg, [default])[0]
        if value is None:
            value = default
        return value

    def _gotCount(self, count, ctx, data):
        # Calculate the last page
        self.lastPage = int((count+self.itemsPerPage)/self.itemsPerPage)
        # Adjust page
        self.page = min(self.page, self.lastPage)
        # Get the items to display
        start = self.itemsPerPage * (self.page-1)
        end = start + self.itemsPerPage
        d = defer.maybeDeferred(self.model.getItems, start, end)
        d.addCallback(self._gotItems, count, ctx, data)
        return d

    def _gotItems(self, items, count, ctx, data):
        # Build and fill slots
        ctx.fillSlots('columnCount', len(self.model.attributes))
        ctx.fillSlots('titleRow', self._titleRow(ctx))
        ctx.fillSlots('dataRows', self._dataRows(items, count))
        # Navigation links
        u = url.URL.fromContext(ctx)
        ctx.fillSlots('page', self.page)
        ctx.fillSlots('lastPage', self.lastPage)
        # Create navigation URLs
        pageArg = self._requestArgName(PAGE)
        start = u.clear(pageArg)
        end = u.replace(self._requestArgName(PAGE), self.lastPage)
        if self.page > 1:
            previous = u.replace(pageArg, max(self.page-1, 1))
        else:
            previous = start
        if self.page < self.lastPage-1:
            next = u.replace(pageArg, min(self.page+1, self.lastPage))
        else:
            next = end
        ctx.fillSlots('start', start)
        ctx.fillSlots('previous', previous)
        ctx.fillSlots('next', next)
        ctx.fillSlots('end', end)
        # Let the super class do the hard work
        return super(TabularView, self).rend(ctx, data)

    def _titleRow(self, ctx):
        # Find the patterns
        titleRow = self._patterns.patternGenerator('titleRow')
        titleCell = self._patterns.patternGenerator('titleCell')
        sortableTitleCell = self._patterns.patternGenerator('sortableTitleCell')
        # Create the row tag
        rowTag = titleRow()
        # Fill the row tag with cell tags
        for col in self.columns:
            # Create the tag
            attribute = self.model.attributes.get(col.attribute)
            if attribute is not None and attribute.sortable:
                cellTag = sortableTitleCell()
            else:
                cellTag = titleCell()
            # Fill the tag
            cellTag.fillSlots('title', col.title)
            sortURL = url.URL.fromContext(ctx)
            sortURL = sortURL.remove(self._requestArgName(PAGE))
            sortURL = sortURL.replace( self._requestArgName(SORT), col.attribute)
            cellTag.fillSlots('asc', sortURL.replace(self._requestArgName(DIR),
                ASC))
            cellTag.fillSlots('desc', sortURL.replace(self._requestArgName(DIR),
                DESC))
            rowTag[cellTag]
        return rowTag

    def _dataRows(self, items, count):
        # Find the patterns
        dataRow = self._patterns.patternGenerator('dataRow')
        dataCell = self._patterns.patternGenerator('dataCell')
        emptyDataRow = self._patterns.patternGenerator('emptyDataRow')

        # Return an empty data row if there are no results
        if not items:
            return emptyDataRow()

        # Create a tag to hold the rows
        rowsTag = tags.invisible()
        for item in items:
            item = itabular.IItem(item)
            rowTag = dataRow()
            rowsTag[rowTag]
            for col in self.columns:
                cellTag = col.rend(self._patterns, item)

#                cellTag = dataCell()
#                cellTag.fillSlots('value',
#                        item.getAttributeValue(col.attribute))
                rowTag[cellTag]

        return rowsTag


class Attribute(object):
    implements(itabular.IAttribute)

    def __init__(self, sortable=False):
        self.sortable = sortable

class DefaultCellRenderer(object):
    implements(itabular.ICellRenderer)

    def rend(self, patterns, item, attribute):

        dataCell = patterns.patternGenerator('dataCell')
        cellTag = dataCell()
        cellTag.fillSlots('value',
                item.getAttributeValue(attribute))
        return cellTag

_defaultCellRenderer = DefaultCellRenderer()

class Column(object):
    implements(itabular.IColumn)

    def __init__(self, attribute, title, renderer=None):
        self.attribute = attribute
        self.title = title
        self.renderer = _defaultCellRenderer
        if renderer:
            self.renderer = renderer

    def rend(self, patterns, item):
        renderer = itabular.ICellRenderer(self.renderer)
        return renderer.rend(patterns, item, self.attribute)


class SequenceListModel(object):
    """
    IModel implementation for sequence-like types.
    """
    implements(itabular.IModel)

    sort = None
    dir = None

    def __init__(self, items):
        self.items = items
        self.attributes = {}

    def setOrder(self, name, dir):
        self.sort = name
        self.dir = dir

    def getItemCount(self):
        return len(self.items)

    def getItems(self, start, end):
        if self.sort is not None:
            # Unfortunately, converting all items to something we can look inside
            # is the only way I can think of to be able to sort.
            items = map(itabular.IItem, self.items)
            comparator = lambda x, y: cmp(x.getAttributeValue(self.sort),
                    y.getAttributeValue(self.sort))
            reverse = (self.dir == 'desc')
            items = sorted(items, cmp=comparator, reverse=reverse)
        else:
            items = self.items
        return items[start:end]


class SequenceRow(object):
    """
    IItem implementation for sequence-like types.
    """
    implements(itabular.IItem)

    def __init__(self, seq):
        self.seq = seq

    def getAttributeValue(self, name):
        name = int(name)
        return self.seq[name]


class MappingRow(object):
    """
    IItem implemenation for mapping-like types.
    """
    implements(itabular.IItem)

    def __init__(self, mapping):
        self.getAttributeValue = mapping.__getitem__


# Register adapters to allow Python's default types to be used.
components.registerAdapter(SequenceListModel, list, itabular.IModel)
components.registerAdapter(SequenceListModel, tuple, itabular.IModel)
components.registerAdapter(SequenceRow, list, itabular.IItem)
components.registerAdapter(SequenceRow, tuple, itabular.IItem)
components.registerAdapter(MappingRow, dict, itabular.IItem)
