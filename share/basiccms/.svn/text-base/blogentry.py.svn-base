from cms.contentitem import Attribute, CMSBase, CMSPluginBase
from cms.contentindex import IndexDefinition
from cms.widgets.richtext import RichText, RichTextArea
from cms.widgets.restsupport import cmsReSTWriter
import formal as forms
from cms.contentitem import Attribute, NonPagishBase, NonPagishPluginBase
from cms.widgets import richtextarea
parsers = [('markdown','MarkDown'),('xhtml','XHTML'),('plain','Plain Text')]


BLOG_ENTRY_PLUGIN_ID = 'brunswick/blogentry'



class BlogEntry(NonPagishBase):

    attributes = [
        Attribute('title', forms.String(required=True), translatable=True),
        Attribute('date', forms.Date(), widgetFactory=forms.widgetFactory(forms.DatePartsInput, dayFirst=True)),
        Attribute('shortDescription', forms.String(required=True), widgetFactory=forms.TextArea, translatable=True),
        Attribute('body', forms.RichTextType(required=True),
            widgetFactory=forms.widgetFactory(richtextarea.RichTextArea, parsers=parsers), translatable=True,
            classes=['imagepicker','gallerypicker','preview','itemselector']),
        Attribute('sidebar', forms.RichTextType(required=True),
            widgetFactory=forms.widgetFactory(richtextarea.RichTextArea, parsers=parsers), translatable=True,
            classes=['imagepicker','gallerypicker','preview','itemselector']),
        ]

    contentIndex = IndexDefinition('title', 'shortDescription', 'body')

    capabilityObjectId = BLOG_ENTRY_PLUGIN_ID

    resourceIds = (BLOG_ENTRY_PLUGIN_ID,)




class BlogEntryPlugin(NonPagishPluginBase):

    name = 'Blog Entry'
    contentItemClass = BlogEntry
    description = 'Blog Entry'
    id = BLOG_ENTRY_PLUGIN_ID
    sort = 'date'
    

    
    
    
    
try:
    from comments import icomments
except ImportError:
    pass
else:
    from zope.interface import implements
    from twisted.python.components import registerAdapter
    class BlogEntryRelatedToSummarizer(object):
        implements(icomments.IRelatedToSummarizer)
        def __init__(self, original):
            self.original = original
        def getTitle(self):
            return self.original.getAttributeValue('title', 'en')
    registerAdapter(BlogEntryRelatedToSummarizer, BlogEntry, icomments.IRelatedToSummarizer)
    
