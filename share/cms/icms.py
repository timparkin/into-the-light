from zope.interface import Interface, Attribute
from nevow import inevow


class IContentItem(Interface):
    pass


class IContentEditor(Interface):
    """Interface for rendering the content item form to edit existing content items.
    """

    def getForm(self, ctx, language, plugin):
        """Called by the framework to get the form to display an existing content item,
        and to allow update of the data.
        """
        pass

    def saveAttributes(self, ctx, form, data, language):
        """Called by the framework to save changes to an existing content item,
        the new data is passed as the data parameter.
        """
        pass

        
class IEditableResourceFactory(Interface):
    """
    Interface for editable resources.
    """

    def createEditableResource(avatar):
        pass


class IImageDataProvider(Interface):
    """
    NOTE: this is deprecated, use IAssetDataProvider
    Interface used by the system image publisher to locate the image data to be
    sent to the browser.
    """

    def provideImageData(avatar, storeSession, name, languages):
        """
        Locate the image data for the named (or None) image, returning a
        (mime-type, data-blob) tuple.
        
        name:
            the name of the image or None for the default image
        languages:
            list of languages to try
        """

class IAssetDataProvider(Interface):
    """
    Interface used by the system image publisher to locate the asset data to be
    sent to the browser.
    """

    def provideData(avatar, storeSession, name, languages):
        """
        Locate the data for the named (or None) asset, returning a
        (mime-type, data-blob) tuple.
        
        name:
            the name of the asset or None for the default asset
        languages:
            list of languages to try
        """

class IPickableAsset(Interface):
    """
    Interface used by the asset browser to identify the names of which assets 
    to browse.
    """

    pickableAssetNames = Attribute("List of asset names to display in the browser")
    
