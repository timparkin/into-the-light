import formal as forms
from cms.contentitem import Attribute, CMSBase, CMSPluginBase
from cms.contentindex import IndexDefinition
from cms.widgets.richtext import RichText, RichTextArea
from cms.widgets.restsupport import cmsReSTWriter
from cms.widgets import richtextarea
from cms.contentitem import Attribute, NonPagishBase, NonPagishPluginBase
parsers = [('markdown','MarkDown'),('xhtml','XHTML'),('plain','Plain Text')]


GALLERY_PLUGIN = 'cms/gallery'



class GalleryItem(NonPagishBase):

    __typename__ = GALLERY_PLUGIN

    attributes = [
        Attribute('title', forms.String(required=True)),
        Attribute('shortDescription', forms.String(required=True),
                widgetFactory=forms.TextArea),
        Attribute('body', forms.RichTextType(required=True),
            widgetFactory=forms.widgetFactory(richtextarea.RichTextArea, parsers=parsers),
            classes=['imagepicker','preview']),
        ]

    contentIndex = IndexDefinition('title', 'shortDescription', 'body')
    capabilityObjectId = GALLERY_PLUGIN
    resourceIds = (GALLERY_PLUGIN,)



class GalleryPlugin(NonPagishPluginBase):

    name = 'Gallery'
    contentItemClass = GalleryItem
    description = 'Gallery'
    id = GALLERY_PLUGIN

