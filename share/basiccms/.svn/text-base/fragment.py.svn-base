"""
A Fragment CMS content type for use in templates
"""


from cms.contentitem import Attribute, NonPagishBase, NonPagishPluginBase
from cms.contentindex import IndexDefinition
from cms.widgets import richtextarea
import formal as forms
parsers = [('markdown','MarkDown'),('xhtml','XHTML'),('plain','Plain Text')]


FRAGMENT_PLUGIN_ID = 'cms/fragment'


class Fragment(NonPagishBase):

    __typename__ = FRAGMENT_PLUGIN_ID

    attributes = [
        Attribute('body', forms.RichTextType(required=True),
            widgetFactory=forms.widgetFactory(richtextarea.RichTextArea, parsers=parsers),
            classes=['imagepicker','preview'],
            ),
        ]

    contentIndex = IndexDefinition('title', 'body')

    capabilityObjectId = FRAGMENT_PLUGIN_ID

    resourceIds = (FRAGMENT_PLUGIN_ID,)



class FragmentPlugin(NonPagishPluginBase):

    name = 'Fragment'
    contentItemClass = Fragment
    description = 'Fragment'
    id = FRAGMENT_PLUGIN_ID
    listable = True
    listTemplates = [('default', 'Default', ''),("div", "Div", "div")]
    templates = [
        ("default", "Default", ""),
        ("div", "Div", "div"),
    ]    
