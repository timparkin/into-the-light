from twisted.internet import defer
from nevow import appserver, static
from crux import skin

from tub.web import page, util


class LoginPage(page.Page):

    componentContent = skin.loader('shell/Login.html', ignoreDocType=True)

    def __init__(self, avatar):
        super(LoginPage, self).__init__()
        self.remember(avatar)

    def locateChild(self, ctx, segments):
        def superResult(result):
            if result is not appserver.NotFound:
                return result
            return self, ()
        d = defer.maybeDeferred(super(LoginPage, self).locateChild, ctx, segments)
        d.addCallback(superResult)
        return d

    child_static = skin.SkinResource()


    def render_openid_form(self, ctx, data):
        # Maybe I don't want to render it
        return ctx.tag



