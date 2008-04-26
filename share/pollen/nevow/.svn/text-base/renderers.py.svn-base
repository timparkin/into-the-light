"""
A collection of useful, general purpose renderers for Nevow templates.
"""

from nevow.url import URL



class RenderersMixin(object):
    """
    A simple mixin class to add all renderers in one go.
    """

    render_if = lambda self, ctx, data: render_if(ctx, data)
    render_remove = lambda self, ctx, data: render_remove(ctx, data)
    render_child_base_href = lambda self, ctx, data: render_child_base_href(ctx, data) 



def render_child_base_href(ctx, data):
    """
    Render a URL that acts as a base for constructing links to child resources.
    In essence, this is url.here with any slashes removed from the end, giving
    it consistent for root and non-root URLs.

    An example of how one might use this to render a link to a child resource is:

        <a href="#"><n:attr name="href"><n:invisible n:render="child_base_href"
            />/<n:slot name="id" /><n:attr>more ...</a>
    """
    url = str(URL.fromContext(ctx))
    url = url.rstrip('/')
    return url



def render_if(ctx, data):
    """
    Conditionally render a tag if the current data tests True.

    The truth test uses Python's standard __nonzero__ protocol.

    By default the renderer will return the tag unchanged or the empty string
    but optional patterns called 'True' and 'False' can be provided to customise
    the output of either condition.
    """

    # Look for (optional) patterns.
    truePatterns = ctx.tag.allPatterns('True')
    falsePatterns = ctx.tag.allPatterns('False')

    # Render the data. If we found patterns use them, otherwise return the tag
    # or nothing.
    if data:
        if truePatterns:
            return truePatterns
        else:
            return ctx.tag
    else:
        if falsePatterns:
            return falsePatterns
        else:
            return ''



def render_remove(ctx, data):
    """
    Unconditionally remove the element from the tree.
    """
    return ''
