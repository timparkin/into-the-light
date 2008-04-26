import formal as forms
from cms.contentitem import Attribute, NonPagishBase, NonPagishPluginBase
from cms.contentindex import IndexDefinition
from cms.widgets import richtextarea
parsers = [('markdown','MarkDown'),('xhtml','XHTML'),('plain','Plain Text')]


NEWS_ITEM_PLUGIN_ID = 'cms/newsitem'



class NewsItem(NonPagishBase):

    __typename__ = NEWS_ITEM_PLUGIN_ID

    attributes = [
        Attribute('title', forms.String(required=True)),
        Attribute('date', forms.Date(required=True),
            widgetFactory=forms.widgetFactory(forms.DatePartsInput,
                dayFirst=True)),
        Attribute('shortDescription', forms.String(required=True),
                widgetFactory=forms.TextArea),
        Attribute('body', forms.RichTextType(required=True),
            widgetFactory=forms.widgetFactory(richtextarea.RichTextArea, parsers=parsers),
            classes=['imagepicker','preview'],
            ),
        ]

    contentIndex = IndexDefinition('title', 'shortDescription', 'body')
    capabilityObjectId = NEWS_ITEM_PLUGIN_ID
    resourceIds = (NEWS_ITEM_PLUGIN_ID,)



class NewsItemPlugin(NonPagishPluginBase):

    name = 'News Item'
    contentItemClass = NewsItem
    description = 'News Item'
    id = NEWS_ITEM_PLUGIN_ID
    templates = [('short', 'Short', 'short'),]
    listable = True
    listTemplates = [('short', 'Short', 'short'),]
    sort= 'date'

