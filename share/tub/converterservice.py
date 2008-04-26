from nevow import inevow
from twisted.python.components import registerAdapter
from pollen import richtext
from zope.interface import implements

def converterFactory():
    return richtext.converterRegistry

class ConverterResource(object):
    implements(inevow.IResource)

    def __init__(self, converterRegistry):
        self.converterRegistry = converterRegistry

    def renderHTTP(self,ctx):
        sourceFormat = ctx.arg('sourceFormat')
        targetFormat = ctx.arg('targetFormat')
        value = ctx.arg('value')
        kwargs = {}
        context = ctx.arg('context',None)
        if context is not None:
            kwargs['context'] = context
        return self.converterRegistry.converter(sourceFormat, targetFormat, **kwargs)(value)
        

registerAdapter(ConverterResource, richtext.RichTextConverterRegistry, inevow.IResource)