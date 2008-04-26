from zope.interface import Attribute, Interface

class IModel(Interface):

    attributes = Attribute('Map of name->column for columns provided by items'
            'of the model')

    def setOrder(attribute, ascending):
        """
        Set the sort attribute and order.
        """

    def getItemCount():
        """
        Return the total number of items in the model.
        """
        
    def getItems(start, end):
        """
        Return a sequence of items between the start and end points.
        """


class IItem(Interface):
    """
    A single item from a model's result.
    """

    def getAttributeValue(name):
        """
        Get the named attribute's value from the item.
        """


class IAttribute(Interface):
    """
    An attribute of a model.
    """
    sortable = Attribute('Boolean flag to indicate the attribute can be used '\
            'for sorting')


class ITabularView(Interface):
    """
    A tabular view of a model.

    The view renders columns that reference model attributes. The view also
    handles paging and basic navigation.
    """
    name = Attribute('Name of the view. Uniquely identifies the view on a page')
    model = Attribute('Data model')
    columns = Attribute('List of columns displayed by the view')
    itemsPerPage = Attribute('Number of items per page')


class IColumn(Interface):
    """
    A column of a tabular view.
    """
    attribute = Attribute('Name of the model attribute to display in the '\
        'column.')
    title = Attribute('Column title')


class ICellRenderer(Interface):
    pass

