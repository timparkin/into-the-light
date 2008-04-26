"""
A common Page CMS content type.
"""


from cms.contentitem import Attribute, CMSBase, CMSPluginBase
from cms.contentindex import IndexDefinition
from cms.widgets.richtext import RichText, RichTextArea
from cms.widgets.restsupport import cmsReSTWriter
import forms


PHOTO_PLUGIN_ID = 'cms/photo'


class Photo(CMSBase):

    __typename__ = PHOTO_PLUGIN_ID

    attributes = [
        Attribute('title', forms.String(required=True)),
        Attribute('shortDescription', forms.String(required=True),
            widgetFactory=forms.TextArea),
        Attribute('body', RichText(required=True),
            widgetFactory=forms.widgetFactory(RichTextArea,
                restWriter=cmsReSTWriter, withImagePicker=True,
                )
            ),
        ]

    contentIndex = IndexDefinition('title', 'shortDescription', 'body')

    capabilityObjectId = PHOTO_PLUGIN_ID

    resourceIds = (PHOTO_PLUGIN_ID,)



class PhotoPlugin(CMSPluginBase):

    name = 'Photo'
    contentItemClass = Photo
    description = 'Photo'
    id = PHOTO_PLUGIN_ID
