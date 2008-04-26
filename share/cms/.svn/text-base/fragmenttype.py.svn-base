"""
A Fragment CMS content type for use in templates
"""
from cms.contentitem import Attribute, NonPagishBase, NonPagishPluginBase
from cms.contentindex import IndexDefinition
import formal as forms


FRAGMENTTYPE_PLUGIN_ID = 'cms/fragmenttype'


class FragmentType(NonPagishBase):

    __typename__ = FRAGMENTTYPE_PLUGIN_ID

    attributes = [
        Attribute('description', forms.String(required=True)),
        Attribute('formDefinition', forms.String(required=True), widgetFactory=forms.TextArea),
        Attribute('template', forms.String(required=True), widgetFactory=forms.TextArea),
        ]

    contentIndex = IndexDefinition('title','description')

    capabilityObjectId = FRAGMENTTYPE_PLUGIN_ID

    resourceIds = (FRAGMENTTYPE_PLUGIN_ID,)



class FragmentTypePlugin(NonPagishPluginBase):

    name = 'FragmentType'
    contentItemClass = FragmentType
    description = 'Fragment Type defines the fields and templates for a fragment'
    id = FRAGMENTTYPE_PLUGIN_ID
  
