import itertools
from nevow import inevow, url, tags as T
from crux import icrux, web, openidconsumer, guard

from tub import itub
from tub.error import TubError
from tub.web import util


class Page(web.Page):
    """
    Base page clas for all pages in a Tub application.
    """

    docFactory = util.PackageTemplate('tub.web.templates', 'TubSkin.html')
    componentContent = None
    
    def __init__(self, original=None, docFactory=None):
        super(Page, self).__init__(original=original, docFactory=docFactory)

    def macro_componentContent(self, ctx):
        if self.componentContent is None:
            raise TubError("componentContent was not provided.")
        return ctx.tag.clear()[lambda ctx, data: self.componentContent]

    def render_pageTitle(self, ctx, data):
        avatar = icrux.IAvatar(ctx, None)
        if avatar is None:
            title = '<no avatar>'
        else:
            title = avatar.realm.title
        ctx.tag.fillSlots('title', title)
        return ctx.tag
        
    def render_tubNavigation(self, ctx, data):
        avatar = itub.IAvatar(ctx, None)
        if avatar is None:
            return ''
        return ComponentNavigationFragment(avatar)

    def render_flashMessage(self, ctx, data):
        request = inevow.IRequest(ctx)
        message = request.args.get('message', [None])[0]
        if message is not None:
            return FlashMessageFragment("message", message)
        message = request.args.get('errormessage', [None])[0]
        if message is not None:
            return FlashMessageFragment("error", message)
        return ''

    
    def render_sso_widget(self, ctx, data):
        if not hasattr(self.avatar, 'user') or not hasattr(self.avatar.user, 'openid'):
            return ''
        sregData = openidconsumer.IOpenIDSReg(inevow.ISession(ctx), None)
        if sregData is None or not self._extractSites(sregData):
            return ''
        else:
            return ctx.tag


    def data_sso_sites(self, ctx, data):
        sregData = openidconsumer.IOpenIDSReg(inevow.ISession(ctx), None)
        return self._extractSites(sregData)


#    def _extractSites(self, sregData):
#        trPattern = 'site_%s_trust_root'
#        lPattern = 'site_%s_label'
#
#        sites = []
#
#        for n in itertools.count():
#            tr = sregData.get(trPattern%n, None)
#            if tr is None:
#                break
#            l = sregData.get(lPattern%n, None)
#            if l is None:
#                break
#            sites.append((tr,l))
#        return sites

    def _extractSites(self, sregData):
        sites = sregData.get('sites', '')
        if not sites:
            return []
        sites = sites.split('|')

        def chunk(seq, count):
            while seq:
             rv = seq[:count]
             seq = seq[count:]
             yield rv
        
        sites = [(r,l) for r,l in chunk(sites, 2)]
        return sites


    def render_sso_site(self, ctx, site):
        u = str(url.URL.fromContext(ctx))
        if u.find(site[0]) != -1:
            ctx.tag(selected="selected")
        ctx.tag.fillSlots('value', url.URL.fromString(site[0]).child(guard.OPENID_AVATAR).add('sreg', 'sites').add('openid', self.avatar.user.openid))
        ctx.tag.fillSlots('label', site[1])
        return ctx.tag
        


class FlashMessageFragment(web.Fragment):

    docFactory = util.PackageTemplate('tub.web.templates',
            'FlashMessage.html')

    def __init__(self, type, message):
        super(FlashMessageFragment, self).__init__()
        self.type = type
        self.message = message

    def render_message(self, ctx, data):
        tag = ctx.tag.onePattern(self.type)
        tag.fillSlots('message', self.message)
        tag.fillSlots("url", url.here)
        return tag


class ComponentNavigationFragment(web.Fragment):
    """
    I render the navigation structure used to access the components installed in
    the application.
    """

    docFactory = util.PackageTemplate('tub.web.templates',
            'ComponentNavigation.html')

    def __init__(self, avatar):
        super(ComponentNavigationFragment, self).__init__()
        self.avatar = avatar

    def render_tree(self, ctx, data):

        leafPattern = ctx.tag.patternGenerator('leaf')
        branchPattern = ctx.tag.patternGenerator('branch')

        def renderComponent(baseURL, component):
            # Calculate the base URL for the component
            url = baseURL.child(component.name)
            # The component may be a package itself
            package = itub.IApplicationPackage(component, None)
            if package is None or not package.getComponents():
                tag = leafPattern()
            else:
                tag = branchPattern()
                tag.fillSlots('children', [renderComponent(url, child) for child
                        in package.getComponents()])
            tag.fillSlots('url', url)
            tag.fillSlots('label', component.label)
            return tag

        ctx.tag.clear()
        apps = self.avatar.applications.iterApplications()
        for app in apps:
            for component in app.getComponents():
                ctx.tag[renderComponent(url.root, component)]
        return ctx.tag

