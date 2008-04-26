from pollen.richtext import converterRegistry

try:
    from markdown import markdown
    def publicMarkdownToXHTMLConverter(text):
        return markdown(text,['cmsimage','cmsitemselection'])
    converterRegistry.register('markdown', 'xhtml', publicMarkdownToXHTMLConverter)
    def adminMarkdownToXHTMLConverter(text):
        return markdown(text,extensions=['cmsimage(context=admin)','cmsitemselection(context=admin)']) 
    converterRegistry.register('markdown', 'xhtml', adminMarkdownToXHTMLConverter, context='admin')
except ImportError:
    raise

try:
    from cms.widgets.restsupport import htmlFragment, cmsReSTWriter
    from basiccms.web.rest import getPublicCmsReSTWriter
    def publicRestToXHTMLConverter(text):
        writer=getPublicCmsReSTWriter()
        return htmlFragment(text, writer=writer)
    converterRegistry.register('rest', 'xhtml', publicRestToXHTMLConverter)
    def adminRestToXHTMLConverter(text):
        return htmlFragment(text, writer=cmsReSTWriter)
    converterRegistry.register('rest', 'xhtml', adminRestToXHTMLConverter,context='admin')
except ImportError:
    pass
