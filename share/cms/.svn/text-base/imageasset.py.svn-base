from zope.interface import implements
from twisted.python import components
import formal as forms
from formal import iformal as iforms, types, TextArea
from cms import icms
from cms.contentitem import Attribute, DefaultContentEditor, populateFormFromPlugin, CMSBase, CMSPluginBase, NonPagishBase, NonPagishPluginBase
from cms.contentindex import IndexDefinition


import warnings
warnings.warn("ImageAsset is deprecated. Use Asset instead", DeprecationWarning, 
        stacklevel=2)


IMAGE_ASSET_PLUGIN_ID = 'cms/image'

class KeyToFileConverter( object ):
    implements( iforms.IFileConvertible )

    def __init__(self, original=None):
        pass

    def fromType( self, value, context = None ):
        pass

    def toType( self, value ):

        if value == None:
            return None

        data = value[1].read()
        return ( value[0], data, value[2] )

class ImageAssetContentEditor( DefaultContentEditor ):
    implements( icms.IContentEditor )

    def getForm(self, ctx, language, plugin, immutable):

        f = forms.Form()
        f.addField('targetUrl', types.String(immutable=True))
        populateFormFromPlugin(f, plugin, immutable)
        f.data = self.original.getAttributeValues(language)
        # Map to a key for the file upload widget
        # Make a URL for the image preview, no bigger than 160x120
        targetUrlWithVersion = plugin.application.services.getService(plugin.assetServiceName).getURLForAsset(self.original)
        targetUrlWithVersion = targetUrlWithVersion.add('size', '160x120')
        targetUrlWithVersion = targetUrlWithVersion.add('nocache', 1)
        # Make a URL that the public site will use
        targetUrlNoVersion = plugin.application.services.getService(plugin.assetServiceName).getURLForAsset(self.original,includeVersion=False)
        f.data['image'] = targetUrlWithVersion
        f.data['targetUrl'] = targetUrlNoVersion
        return f

    def saveAttributes(self, ctx, form, data, language):
        # We need to do some manual file required checking to work around a
        # forms issue.
        if data.get('image') is None and getattr(self.original, 'image', None) is None:
            raise forms.FieldRequiredError('Required', fieldName='image')
        # Copy the original file back if no new file is specified
        if data.get('image') is None:
            data['image'] = self.original.image
        return DefaultContentEditor.saveAttributes(self, ctx, form, data, language)

class ImageAsset(NonPagishBase):
    attributes = [
        Attribute('title', forms.String(required=True), translatable=True),
        Attribute('image', forms.File(), translatable=False, widgetFactory=forms.widgetFactory( forms.FileUploadWidget, convertibleFactory=KeyToFileConverter, originalKeyIsURL=True) ),
        Attribute('shortDescription', forms.String(required=True), translatable=True, widgetFactory=TextArea),
        ]
        
    image = None

    contentIndex = IndexDefinition('title', 'shortDescription')

    resourceIds = (IMAGE_ASSET_PLUGIN_ID,)


class ImageAssetImageDataProvider(object):
    """
    Adapter that allows the imaging service to look inside to get the default
    image.
    """
    implements(icms.IAssetDataProvider)

    def __init__(self, original):
        self.original = original

    def provideData(self, avatar, storeSession, imageName, langs):
        if imageName is not None:
            raise KeyError()
        attrs = self.original.getAttributeValues(langs[0], langs[1:])
        return attrs['image'][:2]


components.registerAdapter(ImageAssetImageDataProvider, ImageAsset,
        icms.IAssetDataProvider)


#class ImageAssetResource(public.Page):
#    docFactory = loaders.xmlfile('templates/public/ImageAsset.html')
#
#    def render_image( self, ctx, item ):
#        from cms.web import systemservices
#        imageurl = systemservices.publicSystemServices.getURLForImage(self.original)
##        ctx.tag.fillSlots( 'imageurl', imageurl )
#        return ctx.tag


class ImageAssetPlugin(NonPagishPluginBase):

    name = 'Image'
    contentItemClass = ImageAsset
    description = 'Image'
    id = IMAGE_ASSET_PLUGIN_ID

    def _adapters( self ):
        return [
            (ImageAssetContentEditor, ImageAsset, icms.IContentEditor)
            ]

    _adapters = property( _adapters )

    def __init__(self, assetServiceName):
        super(ImageAssetPlugin, self).__init__()
        self.assetServiceName = assetServiceName


