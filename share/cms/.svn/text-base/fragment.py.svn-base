"""
A Fragment CMS content type for use in templates
"""
from cms.contentitem import Attribute, NonPagishBase, NonPagishPluginBase
from cms.contentindex import IndexDefinition
import formal as forms


FRAGMENT_PLUGIN_ID = 'cms/fragment'


class Fragment(NonPagishBase):

    __typename__ = FRAGMENT_PLUGIN_ID

    attributes = [
        Attribute('type', forms.String(required=True)),
        Attribute('data', forms.String(), widgetFactory=forms.TextArea),
        ]

    contentIndex = IndexDefinition('title', 'description')

    capabilityObjectId = FRAGMENT_PLUGIN_ID

    resourceIds = (FRAGMENT_PLUGIN_ID,)



class FragmentPlugin(NonPagishPluginBase):

    name = 'Fragment'
    contentItemClass = Fragment
    description = 'Fragment'
    id = FRAGMENT_PLUGIN_ID 
