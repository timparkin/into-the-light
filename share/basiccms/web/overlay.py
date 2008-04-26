""" Site overlay handlers and configuration.  """

from nevow import url, inevow
from crux.icrux import IAvatar
from pollen.nevow import wrappers
from basiccms.web import blog


def blogOverlayHandler(ctx, segments):
    """
    Intercept the blog pages
    """

    if segments[0:2] != ('writing','blog'):
        return None, ()

    return blog.Blog(), segments[2:]



HANDLERS = [blogOverlayHandler]



def install(resource):
    return wrappers.OverlayWrapper(resource, HANDLERS)

