import types
from nevow import context, inevow, stan


class MacroError(Exception):
    pass


class LocateMacroMixin(object):
    """A useful class to mixin to the Page to get macro_* style macro
    location.
    """

    def locateMacro(self, ctx, name):

        # Create a callable factory - a callable that takes no args. This can
        # come from one of a few places:
        #   * A macro_ attribute
        #   * A macro_ callable.
        #   * A call to macroFactory

        attr = getattr(self, 'macro_%s'%name, None)
        if attr is not None:
            # Create the factory
            if isinstance(attr, (types.FunctionType,types.MethodType)):
                factory = lambda: attr(ctx)
            else:
                factory = lambda: attr
        else:
            factory = lambda: self.macroFactory(ctx, name)

        macro = factory()
        if macro is not None:
            return macro

        raise MacroError('Macro %r was not found.'%name)

    def macroFactory(self, ctx, name):
        pass


def findPageContext(ctx):
    """Find the page context.
    """
    while ctx:
        if isinstance(ctx, context.PageContext):
            return ctx
        ctx = ctx.parent


def render_macro(name):

    def _(ctx, data):

        # It would probably be better to have some IMacro interface to
        # locate but the page itself will do for now.
        page = findPageContext(ctx).tag

        # Get the macro.
        macroTag = page.locateMacro(ctx, name)

        # Fill the macro's slots with any available patterns.
        for filler in stan.specials(ctx.tag, 'pattern'):
            macroTag.fillSlots(
                filler._specials['pattern'],
                inevow.IQ(ctx.tag).allPatterns(filler._specials['pattern'])
                )

        # Return the macro
        return macroTag

    return _
