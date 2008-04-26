from nevow import inevow, loaders, util
from poop.store import IStoreSession

from crux import icrux, skin


resource_filename = util.resource_filename


class PackageTemplate(loaders.xmlfile):
    """
    A Nevow xmlfile loader that retrieves the template resource from deep inside
    a Python package.
    """

    def __init__(self, package, filename, **k):
        super(PackageTemplate, self).__init__(util.resource_filename(package,
            filename), **k)


def getStoreSession(ctx):
    """
    Return the store session for the request.
    """
    request = inevow.IRequest(ctx)
    storeSession = request.getComponent(IStoreSession)
    return storeSession


def getAvatar(ctx):
    """
    Locate and return the current avatar.
    """
    return ctx.locate(icrux.IAvatar)



def appendSkinsAndCall(ctx, skins, f, *a, **k):
    """
    Append new skins to any existing skins and call the function, f, with the
    given args.
    """

    if skins:
        # Add the existing skin to the start of the list
        try:
            currentSkin = icrux.ISkin(ctx)
            skins = [currentSkin] + skins
        except TypeError:
            pass
        # Create and remember the new skin
        ctx.remember(skin.CascadingSkin(skins), icrux.ISkin)

    # Call the original function
    return f(*a, **k)

