import formal as forms
#from forms import htmleditor, TextArea
from formal import TextArea

from cms.contentitem import Attribute, CMSBase, CMSPluginBase
from cms.contentindex import IndexDefinition
from cms.widgets.richtext import RichText, RichTextArea
from cms.widgets.restsupport import cmsReSTWriter


PAGE_PLUGIN_ID = 'cms/page'


class Page(PagishBase):

    attributes = [
        Attribute('title', forms.String(required=True), translatable=True),
        Attribute('shortDescription', forms.String(required=True),
                translatable=True, widgetFactory=TextArea),
        Attribute('body', RichText(required=True), translatable=True,
                widgetFactory=forms.widgetFactory(RichTextArea, restWriter=cmsReSTWriter)),
        ]

    contentIndex = IndexDefinition('title', 'shortDescription', 'body')

    capabilityObjectId = PAGE_PLUGIN_ID

    resourceIds = (PAGE_PLUGIN_ID,)


class PagePlugin(PagishPluginBase):

    name = 'Page'
    contentItemClass = Page
    description = 'Page'
    id = PAGE_PLUGIN_ID
