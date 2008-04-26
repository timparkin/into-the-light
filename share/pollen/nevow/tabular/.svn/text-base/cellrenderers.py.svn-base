from types import FunctionType, MethodType
from pollen.nevow.tabular import itabular
from zope.interface import implements
from twisted.python.components import registerAdapter
from nevow import tags as T, entities



class CallableCellRenderer(object):
    """
    Cell renderer that calls a function to fill slots of a tag.

    The function called must have a signature of (tag, item, attribute) and
    should return the tag.
    """

    implements(itabular.ICellRenderer)


    pattern = "dataCell"


    def __init__(self, callable, pattern=None):
        self.callable = callable
        if pattern is not None:
            self.pattern = pattern


    def rend(self, patterns, item, attribute):
        tag = patterns.patternGenerator(self.pattern)()
        tag = self.callable(tag, item, attribute)
        return tag



# Provide adapters to intantiate callable cell renderers from common callable types.
registerAdapter(CallableCellRenderer, FunctionType, itabular.ICellRenderer)
registerAdapter(CallableCellRenderer, MethodType, itabular.ICellRenderer)



class LinkRenderer(CallableCellRenderer):

    def __init__(self, baseURL, idAttribute=None, default=None, pattern=None):
        CallableCellRenderer.__init__(self, self.renderer, pattern=pattern)
        self.baseURL = baseURL
        self.idAttribute = idAttribute
        self.default = default or ' '

    def renderer(self, tag, item, attribute):

        value = item.getAttributeValue(attribute)
        if not value:
            value = self.default

        if self.idAttribute:
            id = item.getAttributeValue(self.idAttribute)
        else:
            id = item.getAttributeValue(attribute)

        if id:
            u = self.baseURL.child(id)
            tag.fillSlots('value', T.a(href=u)[value])
        else:
            tag.fillSlots('value', value)

        return tag


class CheckboxRenderer(object):
    implements(itabular.ICellRenderer)

    def __init__(self, name, pattern=None, valueAttr=None):
        self.pattern = pattern or 'dataCell'
        self.name = name
        self.valueAttr = valueAttr

    def rend(self, patterns, item, attribute):
        cell = patterns.patternGenerator(self.pattern)()
        id = item.getAttributeValue(attribute)
        tag = T.input(type="checkbox", name=self.name, value=id)
        if self.valueAttr:
            value = item.getAttributeValue(self.valueAttr)
            if value:
                tag = tag(checked='checked')
        cell.fillSlots('value', tag)
        return cell

class LookUpRenderer(object):
    implements(itabular.ICellRenderer)

    def __init__(self, options, pattern=None):
        self.pattern = pattern or 'dataCell'
        self.options = options

    def rend(self, patterns, item, attribute):
        cell = patterns.patternGenerator(self.pattern)()
        id = item.getAttributeValue(attribute)
        value = ''
        for k, v in self.options:
            if str(k) == str(id):
                value = v
                break
            
        cell.fillSlots('value', value)
        return cell


