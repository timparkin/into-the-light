from zope.interface import implements
from twisted.internet import defer
from nevow import appserver, inevow, static
from crux import skin

from tub import itub
from tub.web import page, util

import formal as forms


class SystemServicesResource(object):
    implements(inevow.IResource)

    def __init__(self, systemServices):
        self.systemServices = systemServices

    def locateChild(self, ctx, segments):
        try:
            return self.systemServices.getService(segments[0]), segments[1:]
        except KeyError:
            return (None, ())

class RootPage(page.Page):

    addSlash = True
    componentContent = skin.loader('shell/Root.html', ignoreDocType=True)


    def __init__(self, avatar):
        super(RootPage, self).__init__()
        self.remember(avatar)


    def locateChild(self, ctx, segments):

        def superResult(result):
            if result is not appserver.NotFound:
                return result
            return self._locateComponentChild(ctx, segments)

        d = defer.maybeDeferred(super(RootPage, self).locateChild, ctx, segments)
        d.addCallback(superResult)
        return d


    def _locateComponentChild(self, ctx, segments):

        avatar = itub.IAvatar(ctx, None)
        if avatar is None:
            return appserver.NotFound

        try:
            app, component = avatar.applications.componentByName(segments[0])
        except KeyError:
            return appserver.NotFound

        # Build a list of skins provided by the application and/or component.
        skins = [getattr(app, 'skin', None), getattr(component, 'skin', None)]
        skins = [s for s in skins if s]

        try:
            storeSession = util.getStoreSession(ctx)
            return util.appendSkinsAndCall(ctx, skins,
                    component.resourceFactory, avatar, storeSession,
                    segments[1:])
        except TypeError:
            import warnings
            warnings.warn(
                "IApplicationComponent.resourceFactory now takes a storeSession, please update %s."%component.name,
                DeprecationWarning)
            return util.appendSkinsAndCall(ctx, skins,
                    component.resourceFactory, avatar, segments[1:])


    child_static = skin.SkinResource()

    def child_system(self, ctx):
        avatar = itub.IAvatar(ctx, None)
        return SystemServicesResource(avatar.realm.systemServices)


setattr(RootPage, 'child_formsjs', forms.formsJS)

