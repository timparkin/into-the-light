"""
Utilities that should move out of this package to somewhere more useful.
"""

from nevow import inevow, stan, tags, url
from crux import skin, icrux



class RenderFragmentMixin(object):
    """
    Resource mixin that locates and includes a fragment, replacing the element
    with the render="fragment ..." attribute.

    The fragment render method expects a single argument - the name of the
    fragment to include.
    
    If the name looks like a filename then skin.loader is invoked to find an
    XHTML template. Otherwise a method is looked up on the self instance. The
    method should be the name of the fragment with a 'fragment_' preifix.
    """


    def render_fragment(self, name):

        def renderer(ctx, data):
            # If it looks like a filename then load a skin, otherwise look for a
            # named fragment.
            if '.' in name:
                fragment = skin.loader(name, ignoreDocType=True)
            else:
                fragment = getattr(self, 'fragment_%s'%name)
            return fragment

        return renderer



class RenderInheritMixin(object):


    def render_inherit(self, name):

        def renderer(ctx, data):
            # Load the template
#            template = tags.invisible[skin.loader(name, ignoreDocType=True)]
            template = tags.invisible[skin.loader(name)]

            # Fill the inherited template's slots with any available patterns.
            for filler in stan.specials(ctx.tag, 'pattern'):
                template.fillSlots(
                    filler._specials['pattern'],
                    inevow.IQ(ctx.tag).allPatterns(filler._specials['pattern'])
                    )

            return template

        return renderer



class MustBeSecureMixin(object):

    def renderHTTP(self, ctx):
        avatar = icrux.IAvatar(ctx)
        if not avatar.realm.config['public']['checkout_secure']:
            return super(MustBeSecureMixin, self).renderHTTP(ctx)

        request = inevow.IRequest(ctx)
        if request.isSecure():
            return super(MustBeSecureMixin, self).renderHTTP(ctx)
        return url.URL.fromContext(ctx).secure(secure=True)

