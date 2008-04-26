import itertools
from zope.interface import Interface, implements
from twisted.internet import defer
from twisted.python import log
from nevow import appserver, static , inevow, url
from crux import skin, icrux

from tub.public.web import common


class SystemServicesResource(object):
    implements(inevow.IResource)

    def __init__(self, systemServices):
        self.systemServices = systemServices

    def locateChild(self, ctx, segments):
        try:
            if segments[0] == 'system':
                segments = segments[1:]
            return self.systemServices.getService(segments[0]), segments[1:]
        except KeyError:
            return (None, ())



class RootPage(common.CMSPage):

    def __init__(self, avatar, bestMatch = None):
        super(RootPage, self).__init__(avatar)
        self.remember(avatar)
        self.avatar = avatar
        self.bestMatch = bestMatch
        if not self.bestMatch:
            self.bestMatch = simpleBestMatch

    def locateChild(self, ctx, segments):

        avatar = icrux.IAvatar(ctx)
    
        def childLocated(result):
            # :sigh: it might be deferred
            if isinstance(result[0], defer.Deferred):
                result[0].addCallback(lambda r: (r, result[1]))
                result[0].addCallback(childLocated)
                return result[0]
            # Return a sane resource
            if result is not appserver.NotFound and result[0] is not None:
                return result

            # Or look for a CMS managed item.
            return self.bestMatch(ctx, segments)

        # Try to resolve application-fixed resources.
        d = defer.maybeDeferred(super(RootPage, self).locateChild, ctx,
                segments)
        d.addCallback(childLocated)

        return d


    def child_system(self, ctx):
        return SystemServicesResource(self.avatar.realm.systemServices)


    child_skin = skin.SkinResource()



def getSimpleItem(ctx, segments):

    avatar = icrux.IAvatar(ctx)
    storeSession = common.getStoreSession(ctx)

    url = '/' + '/'.join(segments)
    d = avatar.realm.cmsService.getItem(storeSession, avatar, name=url)
    return d



def simpleBestMatch(ctx, segments):

    def gotItem(item):

        if item is None:
            return appserver.NotFound

        # Work out whether the item from CMS can be rendered
        resource = inevow.IResource(item, None)
        if resource is None:
            return appserver.NotFound

        return resource, ()

    d = getSimpleItem(ctx, segments)
    d.addCallback(gotItem)
    return d



class ICurrentNavigationNode(Interface):
    pass

class CurrentNavigationNode(object):
    implements(ICurrentNavigationNode)

    def __init__(self, node):
        self.node = node


def siteMaptItemsForSegments(manager, segments):
    """
    Return a list of matched segments and the list of remaining segments where
    each matched segment is a tuple of (segment, siteMapItem).
    """

    def gotSiteMap(siteMap):
        """Drill into the site map tree matching URL segment to navigation
        node name until we can't go any deeper. Return the deepest node
        and the remaining segments.
        """

        # The root node is the sitemap
        node = siteMap

        # If this is the root node then return the root node as the only
        # matching node.
        if segments == ('',):
            return [('',node)], ()

        # Create a list to accumulate matches.
        # Root is always at the start of the list.
        matches = [('',node)]

        it = iter(segments)
        while True:
            try:
                segment = it.next()
            except StopIteration:
                break
            child = node.findChildByName(segment)
            if child is not None:
                matches.append((segment, child))
                node = child
            else:
                it = itertools.chain([segment], it)
                break

        return matches, list(it)

    d = manager.loadSiteMap()
    d.addCallback(gotSiteMap)
    return d


def getSiteMapManager(ctx):
    avatar = icrux.IAvatar(ctx)
    return avatar.realm.siteMapService.getManager(ctx)


def getItemFromSiteMap(ctx, segments):

    def getMostMatchedItem((matches, segments)):
        # Get the most matched node
        node = matches[-1][1]
        # Remember the node for the navigation
        ctx.remember(CurrentNavigationNode(node), ICurrentNavigationNode)
        # Get the item for the node
        d = node.getItem()
        # Return the node and remaining segments
        d.addCallback(lambda item: (item, segments))
        return d

    manager = getSiteMapManager(ctx)
    d = siteMaptItemsForSegments(manager, segments)
    d.addCallback(getMostMatchedItem)
    return d


def siteMapMatches(ctx, segments):

    def fetchItemsForMatches((matches, segments), manager):
        # Unpack matches to shorten the code below.
        matchedSegments = [m[0] for m in matches]
        matchedItems = [m[1] for m in matches]
        # Prefectch the content items for all sitemap items.
        d = manager.fetchItems(m for m in matchedItems)
        # Get the content items out.
        d.addCallback(lambda ignore: defer.DeferredList([m.getItem() for m in matchedItems]))
        # Throw away the deferred list success/failure status.
        d.addCallback(lambda matchedItems: [m[1] for m in matchedItems])
        # Rebuild 'matches' to return the content items in place of the sitemap items.
        d.addCallback(lambda matchedItems: (zip(matchedSegments, matchedItems), segments))
        return d

    manager = getSiteMapManager(ctx)
    d = siteMaptItemsForSegments(manager, segments)
    d.addCallback(fetchItemsForMatches, manager)
    return d


def siteMapBestMatch(ctx, segments):

    def makeResource((item, segments)):
        if item:
            resource = inevow.IResource(item, None)
            if resource:
                return resource, segments
            log.msg("%r found in sitemap but no resource adapter found"%(item.protectedObject,))
        return appserver.NotFound

    d = getItemFromSiteMap(ctx, segments)
    d.addCallback(makeResource)
    return d

