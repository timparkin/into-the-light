from zope.interface import Attribute, Interface
from crux import icrux


class IApplicationPackage(Interface):
    """
    An application package is an object that contains a number of application
    components. It's the components that actually do something useful.
    """

    def getComponents():
        """
        Get a sequence of application components within the package.
        """
        pass


class IApplication(IApplicationPackage):
    """
    An installable application. An application consists of application metadata
    and a collection of components (because it's also an IApplicationPackage).
    """

    name = Attribute("The identifying name of the application.")
    version = Attribute("The application version.")
    label = Attribute("The short, descriptive name of the application.")
    description = Attribute("Description of what the application does.")
    skin = Attribute("Optional skin to use for the application.")

    def initialize(realm):
        """
        Called when the realm is setup so that the application can do anything
        it needs to do to prepare itself.
        """


class IApplicationComponent(Interface):
    """
    An application component - something that actually does something on behalf
    of an application.
    """

    name = Attribute("Identifying name.")
    label = Attribute("Short, descriptive name.")
    description = Attribute("Description of the component.")
    skin = Attribute("Optional skin to use for the component.")

    def resourceFactory(avatar, storeSession, segments):
        """
        Create the component's resource, returning a tuple of (resource,
        remainingSegments).
        """


class IRealm(icrux.IRealm):
    """
    Tub realm.
    """
    title = Attribute("Descriptive title of the application.")
    store = Attribute("Database store")


class IAvatar(icrux.IAvatar):
    """
    Tub-specific avatar interface.
    """

