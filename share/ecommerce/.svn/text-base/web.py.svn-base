from nevow import loaders, url #, util

from tub.web import page, util


def loader(filename):
    return loaders.xmlfile(util.resource_filename('ecommerce.templates',
        filename), ignoreDocType=True)



class ApplicationsPage(page.Page):
    """Page used for listing ecommerce applications."""
    componentContent = loader('Applications.html')

    def __init__(self, parent):
        super(ApplicationsPage, self).__init__()
        self.parent = parent

    def data_applications(self, ctx, data):
        return self.parent.getComponents()

    def render_application(self, ctx, application):
        """Render a user instance.
        """
        ctx.tag.fillSlots('href', url.URL.fromContext(ctx).child(application.name))
        ctx.tag.fillSlots('label', application.label)
        return ctx.tag

    def child_system(self, ctx):
        return self.parent.services
