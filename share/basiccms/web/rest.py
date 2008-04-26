from docutils.writers.html4css1 import Writer
from nevow import flat, loaders, inevow, rend

from crux import skin

from cms.widgets.itemselection import ItemSelection
from cms.widgets.restsupport import CMSReST2HTMLTranslator, CMSReST2HTMLTranslatorPublic, htmlFragment



class PublicReSTTranslator(CMSReST2HTMLTranslatorPublic):


    def visit_cmsitemselection_node(self, node):
        encodedItemsel=node.attributes['itemsel']
        itemsel = ItemSelection.fromString(str(encodedItemsel))
        if itemsel.id:
            # Individual item
            htmlFragment = """
            <n:invisible n:data="cmsitemselection %(itemsel)s" n:render="cmsitemselection %(itemsel)s" />
            """%{'itemsel': encodedItemsel}
        elif itemsel.paging:
            # List with paging tags
            htmlFragment = """
            <n:invisible n:data="cmsitemselection %(itemsel)s" n:render="paging %(itemsPerPage)s" >
              <n:invisible n:pattern="item" n:render="cmsitemselection %(itemsel)s" />
            </n:invisible>
            <n:invisible n:render="fragment paging_controls" />
            """%{'itemsel': encodedItemsel, 'itemsPerPage':itemsel.paging}
        else:
            # List without paging
            htmlFragment = """
            <n:invisible n:data="cmsitemselection %(itemsel)s" n:render="sequence" >
              <n:invisible n:pattern="item" n:render="cmsitemselection %(itemsel)s" />
            </n:invisible>
            """%{'itemsel': encodedItemsel}
        classes=node.attributes.get('classes')
        if classes:
            htmlFragment = """<div class="%s cmsitems">%s</div>"""%(" ".join(classes), htmlFragment)
        self.body.append(htmlFragment)


    def depart_cmsitemselection_node(self, node):
        pass



_PublicCmsReSTWriter = None
_PublicReSTTranslator = PublicReSTTranslator


def setPublicReSTTranslator(publicReSTTranslator):
    global _PublicCmsReSTWriter, _PublicReSTTranslator

    if _PublicCmsReSTWriter:
        raise Exception("PublicCMSReSTWriter has been created")
    _PublicReSTTranslator = publicReSTTranslator


def getPublicCmsReSTWriter():

    global _PublicCmsReSTWriter, _PublicReSTTranslator

    if not _PublicCmsReSTWriter:
        _PublicCmsReSTWriter = Writer()
        _PublicCmsReSTWriter.translator_class = _PublicReSTTranslator

    return _PublicCmsReSTWriter



def RichTextFlattener(original, ctx):
    xml = original.htmlFragment(restWriter=getPublicCmsReSTWriter())
    return _xml2ReSTFragment(xml)

from cms.widgets import richtext
if flat.getFlattener(richtext.RichTextData(None)):
    raise '*** Rich Text Flattener already registered'
flat.registerFlattener(RichTextFlattener, richtext.RichTextData)



def str2ReSTFragment(str):
    xml = htmlFragment(str, writer=getPublicCmsReSTWriter())
    return _xml2ReSTFragment(xml)



def _xml2ReSTFragment(xml):
    XML_TEMPLATE = """<!DOCTYPE html
      PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
      "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
      <div xmlns:n="http://nevow.com/ns/nevow/0.1" >%(xml)s</div>"""
    xml = XML_TEMPLATE%{'xml':xml}
    return ReSTFragment(docFactory=loaders.xmlstr( xml, ignoreDocType=True))



from basiccms.web import common
class ReSTFragment(rend.Fragment, common.PagingMixin, skin.SkinRenderersMixin):
    def data_cmsitemselection(self, encodedItemsel):
        return data_cmsitemselection(encodedItemsel)
    def render_cmsitemselection(self, encodedItemsel):
        return render_cmsitemselection(encodedItemsel)

def data_cmsitemselection(encodedItemsel):

    def data(ctx, data):

        def gotData(data, ctx):
            if hasattr(data, 'sort'):
                try:
                    data.sort(key=lambda i: i.date, reverse=True)
                except AttributeError:
                    data.sort(key=lambda i: i.name, reverse=True)
                    
            return data

        itemsel = ItemSelection.fromString(str(encodedItemsel))
        d = inevow.IGettable(itemsel).get(ctx)
        d.addCallback(gotData, ctx)
        return d

    return data


def render_cmsitemselection(encodedItemsel):
    itemsel = ItemSelection.fromString(str(encodedItemsel))

    def renderer(ctx, data):
        from basiccms.web import cmsresources
        resource = inevow.IResource(data)
        if itemsel.template is not None and hasattr(resource, 'setTemplate'): 
            resource.setTemplate(*cmsresources.parseTemplateString(itemsel.template))
        return resource

    return renderer


