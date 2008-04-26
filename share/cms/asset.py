from zope.interface import implements
from twisted.python import components
import formal as forms
from formal import iformal as iforms, types, TextArea
from cms import icms
from cms.contentitem import Attribute, DefaultContentEditor, populateFormFromPlugin, CMSBase, CMSPluginBase, NonPagishBase, NonPagishPluginBase
from cms.contentindex import IndexDefinition

from cms import contenttypeutil

ASSET_PLUGIN_ID = 'cms/asset'

class AssetContentEditor( contenttypeutil.ContentEditor ):
    assetNames = ('asset', )

    def getForm(self, ctx, language, plugin, immutable):
        # I want to put the asset id at the top of the form in an immutable
        # field
        form = forms.Form()
        form.addField('assetId', types.String(immutable=True))
        populateFormFromPlugin(form, plugin, immutable)
        form.data = self.original.getAttributeValues(language)
        form.data['assetId'] = self.original.id
        self.updateFormAssets(plugin, form)
        return form


class Asset(NonPagishBase):
    implements(icms.IPickableAsset)

    attributes = [
        Attribute('title', forms.String(), translatable=True),
        Attribute('asset', forms.File(), translatable=False, widgetFactory=forms.widgetFactory( forms.FileUploadWidget, convertibleFactory=contenttypeutil.KeyToFileConverter, originalKeyIsURL=True) ),
        Attribute('shortDescription', forms.String(), translatable=True, widgetFactory=TextArea),
        ]
        
    image = None

    contentIndex = IndexDefinition('title', 'shortDescription')

    resourceIds = (ASSET_PLUGIN_ID,)

    pickableAssetNames = ['asset']

class AssetDataProvider(contenttypeutil.AssetDataProvider):

    defaultAssetName = 'asset'

components.registerAdapter(AssetDataProvider, Asset,
        icms.IAssetDataProvider)


class AssetPlugin(NonPagishPluginBase):

    name = 'Asset'
    contentItemClass = Asset
    description = 'Asset'
    id = ASSET_PLUGIN_ID

    def _adapters( self ):
        return [
            (AssetContentEditor, Asset, icms.IContentEditor)
            ]

    _adapters = property( _adapters )

    def __init__(self, assetServiceName):
        super(AssetPlugin, self).__init__()
        self.assetServiceName = assetServiceName

