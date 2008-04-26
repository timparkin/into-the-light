"""
A common Page CMS content type.
"""


from cms.contentitem import Attribute, PagishBase, PagishPluginBase
from cms.contentindex import IndexDefinition
from cms.widgets import richtextarea
import formal as forms
from basiccms import fragment, news
parsers = [('markdown','MarkDown'),('xhtml','XHTML'),('plain','Plain Text')]


PAGE_PLUGIN_ID = 'cms/page'


class Page(PagishBase):

    __typename__ = PAGE_PLUGIN_ID

    attributes = [
        Attribute('title', forms.String(required=True)),
        Attribute('shortDescription', forms.String(required=True),
            widgetFactory=forms.TextArea),
        Attribute('body', forms.RichTextType(required=True),
            widgetFactory=forms.widgetFactory(richtextarea.RichTextArea, parsers=parsers,itemTypes=[fragment.Fragment,news.NewsItem]),
            classes=['imagepicker','gallerypicker','preview','itemselector'],
            ),
        Attribute('sidebar', forms.RichTextType(),
            widgetFactory=forms.widgetFactory(richtextarea.RichTextArea, parsers=parsers,itemTypes=[fragment.Fragment,news.NewsItem]),
            classes=['imagepicker','gallerypicker','preview','itemselector'],
            ),
        ]

    contentIndex = IndexDefinition('title', 'shortDescription', 'body')

    capabilityObjectId = PAGE_PLUGIN_ID

    resourceIds = (PAGE_PLUGIN_ID,)



class PagePlugin(PagishPluginBase):

    name = 'Page'
    contentItemClass = Page
    description = 'Page'
    id = PAGE_PLUGIN_ID
    templates=[
        ('default','Default','default,class=default'),
        ('homepage','Home Page','homepage,class=homepage'),
        ('widecontent','Wide Content','widecontent,class=widecontent'),
        ]

