import cgi

class RichTextConverterRegistry:

    def __init__(self):
        self.registry = {}
    
    def register(self, sourceFormat, targetFormat, converter, context=None):
        self.registry[(sourceFormat,targetFormat,context)] = converter

    def converter(self, sourceFormat, targetFormat, context=None):
        if sourceFormat == targetFormat:
            return lambda source: source
        try:
            return self.registry[(sourceFormat,targetFormat,context)]
        except KeyError:
            return self.registry[(sourceFormat,targetFormat,None)]

def plainTextToXHTMLConverter(text):
    return cgi.escape(text)


converterRegistry = RichTextConverterRegistry()
converterRegistry.register('plain', 'xhtml', plainTextToXHTMLConverter)

converter = converterRegistry.converter
