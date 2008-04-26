from nevow import context, inevow, url as U, tags as T, stan
from zope.interface import implements, Interface, Attribute
from twisted.python.components import registerAdapter

class IBreadcrumb(Interface):
    
    trail = Attribute("""The breadcrumb""")

    def add(self, url, label):
        """Add a segment to the breacrumb with a given (optional) url and label"""
    

class Breadcrumb(object):
    implements (IBreadcrumb)
    
    def __init__(self):	
        self.trail = []
    
    def add(self, url, label):
        self.trail.append((url,label))
        

def add(ctx, label, url=None, segments=None):
    '''Helper function to add to the breadcrumb.
    '''
    # Construct the URL
    if url is None:
        url = U.URL.fromContext(inevow.IRequest(ctx))

    # Add any segments
    for seg in segments or []:
        url = url.child(seg)
    
    # Add the breadcrumb
    bc = IBreadcrumb(ctx)
    bc.add(url, label)
    
    
def breadcrumbFactory(ctx):
    request = inevow.IRequest(ctx)
    breadcrumb = request.getComponent(IBreadcrumb)
    if breadcrumb is None:
        breadcrumb = Breadcrumb()
        request.setComponent(IBreadcrumb, breadcrumb)
    return breadcrumb


def breadcrumbRenderer(ctx, includesHome=False):
    
    itemPatternFactory = ctx.tag.patternGenerator('item')
    try :
        firstPattern = ctx.tag.onePattern('first')
    except stan.NodeNotFound:
        firstPattern = itemPatternFactory()
    try:
        lastPattern = ctx.tag.onePattern('last')
    except stan.NodeNotFound:
        lastPattern = itemPatternFactory()

    if includesHome is False:
        firstPattern.fillSlots('url', U.URL.fromString('/'))
        firstPattern.fillSlots('label', 'Home')
        yield firstPattern
    
    trail = IBreadcrumb(ctx).trail
    for segment in trail[:-1]:
        itemPattern = itemPatternFactory()
        itemPattern.fillSlots('url', segment[0])
        itemPattern.fillSlots('label', segment[1])
        yield itemPattern
    
    if len(trail) > 0:
        lastSegment = trail[-1]
        lastPattern.fillSlots('url', lastSegment[0])
        lastPattern.fillSlots('label', lastSegment[1])
        yield lastPattern  
    
    
registerAdapter(breadcrumbFactory, context.RequestContext, IBreadcrumb)

