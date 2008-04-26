from tub.public.web import pages
from crux import web, icrux
from twisted.internet import defer
from nevow import loaders, rend, url, context, tags as T
from sitemap import isitemap

class NestedListNavigationFragment(rend.Fragment):
    docFactory = loaders.stan(T.ul(class_='navigation',render=T.directive('navigation')))

    def __init__(self, type=None, maxdepth=None, showroot=False, openall=False,
            openallbelow=0, startdepth=0):
        """

        Parameters
        ----------

        type    
            If set, filters the navigation items in sitemap to be of the given
            type only. Otherwise, all navigation items (not necessarily the
            same as all sitemap items) are rendered.

        startdepth
            Depth at which to start showing navigation items. Can be an
            absolute or relative depth (see below).

        maxdepth
            Maximum depth of navigation items to show. Can be an absolute or
            relative depth (see below).

        showroot
            Flag to say whether the 'root' of the current tree should be shown
            (e.g. home for a general menu)

        openallbelow
            Open every submenu below the given depth (good for leaving top
            level closed but showing all submenus within a section).

        openall
            Flag to override the openallbelow to expand every menu.


        URL Depth Specification
        -----------------------

        The startdepth and maxdepth can be specified in a number of ways,
        either absolute to the root URL or relative from a symbolic location or
        a named navigation level.

            <int>   
                Absolute depth from the root of the site.

            here+<int>
                Relative to the current URL.

            startdepth+<int>
                Relative to the startdepth. (Don't use for startdepth itself!)

            <navigation>+<int>
                Relative to the deepest item in the given navigation level.
        """
        super(NestedListNavigationFragment,self).__init__()
        self.navigationType = type
        self.startdepth = startdepth
        self.maxdepth= maxdepth
        self.showroot = showroot
        self.openall = openall
        self.openallbelow = openallbelow


    def resolveArgs(self, siteMap, ctx):
        """
        Resolve the args passed to __init__ to have real meaning in the context
        of the navigation and current location in the URL.
        
        We also perform some type checking at the same time to ensure later
        comparisons work correctly.
        """

        if self.navigationType is not None:
            self.navigationType = int(self.navigationType)
        if self.maxdepth is not None:
            self.maxdepth = self.resolveDepthArg(self.maxdepth, siteMap, ctx)
        self.startdepth = self.resolveDepthArg(self.startdepth, siteMap, ctx)
        self.showroot = bool(self.showroot)
        self.openall = bool(self.openall)
        self.openallbelow = int(self.openallbelow)

        return siteMap


    def resolveDepthArg(self, depthSpec, siteMap, ctx):
        """
        Resolve a depth arg.
        """
        # Convert to a string to test, even though we may simply turn it back
        # into an integer.
        depthSpec = str(depthSpec)

        # If there is no '+' then it's just an integer.
        if '+' not in depthSpec:
            return int(depthSpec)

        # Split the spec
        relativeTo, relativeOffset = depthSpec.split('+', 1)
        relativeOffset = int(relativeOffset)

        if relativeTo == 'here':
            # Relative to the current url
            relativeDepth = len(self._getCurrentPath(siteMap, ctx)) - 1

        elif relativeTo == 'startdepth':
            # Relative to the start depth
            relativeDepth = self.resolveDepthArg(self.startdepth, siteMap, ctx)

        else:
            # Relative to the navigation level
            navigationLevel = int(relativeTo)
            relativeDepth = len(self._getCurrentPath(siteMap, ctx, navigationLevel)) - 1

        return relativeDepth + relativeOffset
        
    
    def render_navigation(self, ctx, data):
        avatar = icrux.IAvatar(ctx)
        d = avatar.realm.siteMapService.getManager(ctx).loadSiteMap()
        d.addCallback(self._fetchItems, ctx, avatar)
        d.addCallback(self.resolveArgs, ctx)
        d.addCallback(self._gotSiteMap, ctx)
        return d

    def _getCurrentPath(self, siteMap, ctx, navigationLevel=None):

        try:
            node = ctx.locate(pages.ICurrentNavigationNode).node
        except KeyError:
            node = siteMap

        # Split the node's path
        path = node.path.split('.')

        # Rebuild path to reference the deepest path within the given
        # navigation level (if any).
        if navigationLevel is not None:
            path, rest = path[:1], path[1:]
            node = siteMap
            for segment in rest:
                node = node.findChildByName(segment)
                if node.level == navigationLevel:
                    path.append(segment)
                else:
                    break

        return path

    def _fetchItems(self, siteMap, ctx, avatar):
        # Items are not loaded by the site map by default, they
        # are loaded on demand (if they haven't already been loaded).
        # When building navigation we need several items (we need to
        # know the title of the item) but loading items individually 
        # would be slow so work out which items we will need and
        # load them in one go.
        self.siteMap = siteMap
        self.currentPath = self._getCurrentPath(siteMap, ctx)

        items = itemsToDisplay(self.siteMap, self.currentPath, self.navigationType)

        d = avatar.realm.siteMapService.getManager(ctx).fetchItems(items)
        d.addCallback(lambda ignore: siteMap)
        return d

    def _gotSiteMap(self, siteMap, ctx):

        # Highlighting of navigation is driven by the request.
        requestPath = ['root'] + url.URL.fromString(context.IRequest(ctx).path).pathList()
        # Filter out empty segments
        requestPath = [ r for r in requestPath if r ]

        def urlForNode(node):
            u = url.root
            for segment in node.path.split('.')[1:]:
                u = u.child(segment)
            return u

        def gotRoot(item,tag):

            nodepath = node.path.split('.')
            nodedepth = len(nodepath)            

            try:
                title = node.label
            except TypeError:
                return defer.succeed('')

            t = T.li()[T.a(href=urlForNode(node))[title]]
            tag[t]
            
            if requestPath == nodepath:
                t = t(class_="selected")            

            return defer.succeed(tag)


        def gotItem(item, tag, node, urlpath):

            nodepath = node.path.split('.')
            nodedepth = len(nodepath)

            try:
                title = node.label
            except TypeError:
                return defer.succeed('')

            # If we're not showing submenus (apart from the selected item)
            # then loop through our urlpath and check that the node matches each segment.
            # If it doesn't then return our result so far
            if not self.openall:
                for n, segment in enumerate(urlpath[:self.openallbelow]):
                    if n+1>=nodedepth or segment != nodepath[n+1]:
                        return defer.succeed(tag)

            t = T.li()[T.a(href=urlForNode(node))[title]]
            tag[t]

            # Mark selected item
            if requestPath[:nodedepth] == nodepath[:nodedepth]:
                t = t(class_="selectedpath")
            if requestPath == nodepath:
                t = t(class_="selected")

            # only show up to a set depth
            if self.maxdepth is not None and nodedepth > self.maxdepth:
                return defer.succeed(tag)

            if node.children and (self.openall or requestPath[:nodedepth] == nodepath[:nodedepth]):

                s = T.ul()
                t[s]
                d = addChildren(s, node, urlpath,isRoot=False)
            else:
                d = defer.succeed(tag)
                
            return d

        @defer.deferredGenerator
        def addChildren(tag, node, urlpath, isRoot=True):
            """ The root node is the top level segment (e.g. for an absolute url
                /a/b/c, root node is 'a'
                node is the sitemap root node (with path 'root')
            """

            # if this is the root node of our tree, and we have 'showroot' set
            # then add this as a top level list item
            if node is not None and isRoot is True and self.showroot is True:
                d = node.getItem()
                d.addCallback(gotRoot, tag)
                d = defer.waitForDeferred(d)
                yield d
                d.getResult()

            if node is None or node.children is None:
                yield tag
                return

            # for each child of the node, (i.e. for each top level menu item) 
            for child in node.children:
                # as long as a level is defined, otherwise continue
                if self.navigationType is not None and child.level != self.navigationType:
                    continue
                d = child.getItem()
                d.addCallback(gotItem, tag, child, urlpath)
                d = defer.waitForDeferred(d)
                yield d
                d.getResult()

            yield tag

        def menuBuilt(tag):

            def appendClassAttribute(tag, attribute, value):
                tag.attributes[attribute] = "%s %s"%(tag.attributes.get('class', ''),value)

            
            try:
                appendClassAttribute(tag.children[0], 'class', 'first-child')
                appendClassAttribute(tag.children[-1], 'class', 'last-child')
            except IndexError:
                pass
            
            for n,child in enumerate(tag.children):
                appendClassAttribute(tag.children[n], 'class', 'item-%s'%(n+1))
            return tag


        # Render from the root of the sitemap by default
        node = siteMap

        # Adjust the root node for the start depth.
        urlpath = list(url.URL.fromString(context.IRequest(ctx).path).pathList())
        if urlpath == ['']:
            urlpath = []

        if len(urlpath) < self.startdepth:
            # We've not reached this section of the site yet.
            node = None
        else:
            # Traverse the sitemap to find the root node at the given start depth.
            for segment in urlpath[:self.startdepth]:
                node = node.findChildByName(segment)


        # We always start with a menu
        tag = T.ul()
        

        # Take the rootnode and add children given the navigation level as
        # context (navlevel is primary secondary but coded as integers)
        d = addChildren(tag, node, urlpath)
        d.addCallback(menuBuilt)
        return d
    
def itemsToDisplay(siteMap, currentPath, navigationType):

    # root is always displayed
    items = [siteMap]

    currentPathDepth = len(currentPath)

    def visitChildren(node):

        if node is None or node.children is None:
            return

        # Add the children of the node
        for child in node.children:
            if child.level is not None:
                items.append(child)

        nodepath = node.path.split('.')
        nodedepth = len(nodepath)

        if nodedepth == currentPathDepth:
            return

        child = currentPath[nodedepth]
        visitChildren(node.findChildByName(child))

    visitChildren(siteMap)

    return items
    
