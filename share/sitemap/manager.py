import itertools
from os.path import join as opj
from datetime import datetime
from twisted.internet import defer
from twisted.python import log
from poop import objstore
from nevow import compy as components
import exceptions
from tub.capabilities import GroupPermission, CommonPermissions, requiredPermissions
from tub import error, hierarchyutil

class SiteMapItem(object):
    """I represent a site map item aka a menu item.
    """

    def __init__(self, manager, id, label, path, level, app, itemId, children=None):
        self.manager = manager
        self.id = id
        self.path = path
        self.level = level
        self.app = app
        self.itemId = itemId
        self.label = label
        self._item = None
        if children is not None:
            self.children = children
        else:
            self.children = []

    def name():
        def get(self):
            return self.path.split('.')[-1]
        def set(self, newName):
            self.path = '.'.join(self.path.split('.')[:-1]+[newName,])
        return property(get, set)
    name = name()

    def findChildById(self, childId):
        """Search all the children of this node for a child with the specified
        id.
        """
        for child in self.children:
            if child.id == childId:
                return child
            child = child.findChildById(childId)
            if child is not None:
                return child

    def findChildByName(self, name):
        """Find an immediate child with the specified name.
        """
        for child in self.children:
            if child.name == name:
                return child

    def getItem(self):

        if self._item:
            return defer.succeed(self._item)

        def gotItem(item):
            self._item = None
            if item and len(item) > 0:
                self._item = item[0]
            return self._item

        d = self.manager.getItem(self.app, self.itemId)
        d.addCallback(gotItem)
        return d

    def hasItem(self):
        return self._item is not None

    def setItem(self, item):
        self._item = item
        
        
    def getNodeFromUrl(self,childUrl):
        if childUrl.startswith('/'):
            childUrl = childUrl[1:]
        segments = childUrl.split('/')
        node = self
        for segment in segments:
            for n in node.children:
                if n.path.split('.')[-1] == segment:
                    node = n
                    break
            else:
                return None
        if n != self:
            return n
        else:
            return None

CAPABILITY_SITEMAP_MGR_ALIAS = 'sitemap/sitemap'

UPDATE_SITEMAP = GroupPermission(CommonPermissions.UPDATE,
    CAPABILITY_SITEMAP_MGR_ALIAS)

NOCHANGE=object()

class SiteMapManager(object):
    """Site Map storage implementation.
    """

    name = 'sitemap'
    description = 'Site Map Manager'

    def __init__(self, avatar, storeSession, sources, reservedNodes=None, navigationLevels=None):
        self.avatar = avatar
        self.storeSession = storeSession
        self.sources = sources
        self.reservedNodes = reservedNodes
        self.navigationLevels = navigationLevels
        self._names = None
        self._siteMap = None

    def getNamesOfItems(self):
        # Returned cached names if I've got them

        def gotNames(names):
            self._names = names
            return names

        if self._names:
            return defer.succeed(self._names)

        d = self._getNames()
        d.addCallback(gotNames)
        return d

    @defer.deferredGenerator
    def _getNames(self):
        def gotNames(names, app):
            return [(app, id, name) for id, name in names]

        rv = []
        for k, v in self.sources.iteritems():
            d = v.getNamesOfItems(self.avatar, self.storeSession)
            d.addCallback(gotNames, k)
            d = defer.waitForDeferred(d)
            yield d
            rv = rv + d.getResult()

        rv.sort(lambda f, s: cmp(f[2], s[2]))
        yield rv

    def getItem(self, app, id):

        itemFactory = self.sources.get(app, None)
        if not itemFactory:
            log.msg('SiteMap.getItem; no source for app %s'%app)
            return defer.succeed(None)

        return itemFactory.findItemsByIds(self.avatar, self.storeSession, [id])

    @defer.deferredGenerator
    def fetchItems(self, siteMapItems):

        def gotAppItems(appItems, siteMapItems):
            for appItem in appItems:
                for siteMapItem in siteMapItems:
                    if appItem.id == siteMapItem.itemId:
                        siteMapItem.setItem(appItem)

        itemAppMap = {}
        for item in siteMapItems:
            if item.hasItem():
                continue
            itemAppMap.setdefault(item.app, []).append(item)

        for app, siteMapItems in itemAppMap.iteritems():
            d = self.sources[app].findItemsByIds(self.avatar, self.storeSession,
                [i.itemId for i in siteMapItems])
            d.addCallback(gotAppItems, siteMapItems)
            d = defer.waitForDeferred(d)
            yield d
            d.getResult()


    def loadSiteMap(self):
        if self._siteMap:
            return defer.succeed(self._siteMap)

        def gotSiteMap(siteMap):
            self._siteMap = siteMap
            return self._siteMap

        d = self._fetchNavRows(public=False)
        d.addCallback(self._rowsToTree)
        d.addCallback(gotSiteMap)
        return d

    def _fetchNavRows(self, public=None):
        # Force the public arg to be passed to be safe
        assert public is not None

        sql = """
            select
                s.id, s.textid, s.label, s.path, nlevel(s.path) as depth, s.ord, s.level,
                si.app, si.item_id
            from sitemap as s
            join sitemap_item as si on s.id = si.sitemap_id
            order by nlevel(s.path), s.ord
            """
        d = self.storeSession.curs.execute(sql)
        d.addCallback(lambda ignore: self.storeSession.curs.fetchall())
        return d

    def _rowsToTree(self, rows):

        def parentPath(path):
            return '.'.join(path.split('.')[:-1])

        # Create a dict for tracking the node for a particular path.
        pathToNodeMap = {}

        for row in rows:

            # Unpack the row.
            id, textId, label, path, depth, seq, level, app, itemId = row

            # Create a node and add it to the map.
            node = SiteMapItem(self, id, label, path, level, app, itemId)
            pathToNodeMap[path] = node

            # If the node should have a parent then find the parent node
            # and add the new node as a child.
            if depth > 1:
                # Find the parent node and add it as a child
                parentNode = pathToNodeMap.get(parentPath(path),None)
                if parentNode:
                    parentNode.children.append(node)
                    node.parent = parentNode

        # Return the "root" node.
        if pathToNodeMap.has_key('root'):
            return pathToNodeMap['root']
        else:
            return None
    # ----------

    @requiredPermissions(UPDATE_SITEMAP)
    def updateNode(self, node, app, itemId, name=NOCHANGE, level=NOCHANGE, label=NOCHANGE):

        def updateMem():
            # Update the node too
            node.itemId = itemId
            node.app = app
            if name is not NOCHANGE:
                node.name = name

        d = self._updateNodeContentItem(node, app, itemId)
        if name is not NOCHANGE:
            d.addCallback(lambda r: self._updateNodeName(node, name))
        if level is not NOCHANGE:
            d.addCallback(lambda r: self._updateNodeLevel(node, level))
        if label is not NOCHANGE:
            print 'updating label'
            d.addCallback(lambda r: self._updateNodeLabel(node, label))
        d.addCallback(lambda r: updateMem())
        return d

    @requiredPermissions(UPDATE_SITEMAP)
    @defer.deferredGenerator
    def addChildToNode(self, node, childName, label, app, itemId, level):
        # Need to check whether the childName already exists,
        # Ideally this should be done on the database (and there is a
        # risk that someone else may add the same childName after I've
        # checked). But pgasync currently closes the connection on error
        # and it's not easy to get a sensible error message out of the
        # stored procedure with it erroring.
        curs = self.storeSession.curs

        d = defer.waitForDeferred( hierarchyutil.isUniquePath( curs,
            'sitemap', 'path', node.path, childName ) )
        yield d

        if not d.getResult():
            raise error.NotUniqueError()

        d = curs.callproc('insert_node_under', ('sitemap', node.path, childName, childName, label))
        d.addCallback(lambda ignore: curs.fetchone())
        d = defer.waitForDeferred(d)
        yield d
        nodeId = d.getResult()[0]

        d = curs.execute(
            "update sitemap set level=%(level)s where id=%(id)s",
            {'level': level, 'id': nodeId}
            )
        d.addCallback(lambda ignore: curs.execute(
            "insert into sitemap_item (sitemap_id,item_id,app) values (%s, %s,%s)",
            (nodeId, itemId, app)
            ))
        d = defer.waitForDeferred(d)
        yield d
        d.getResult()
        yield None

    @requiredPermissions(UPDATE_SITEMAP)
    @defer.deferredGenerator
    def insertRootNode(self, name, label, app, itemId, level):
        # we're using insert root node to create the top element in the sitemap
        curs = self.storeSession.curs

        d = curs.callproc('insert_root_node', ('sitemap', name, name, label))
        d.addCallback(lambda ignore: curs.fetchone())
        d = defer.waitForDeferred(d)
        yield d
        nodeId = d.getResult()[0]

        d = curs.execute(
            "update sitemap set level=%(level)s where id=%(id)s",
            {'level': level, 'id': nodeId}
            )
        d.addCallback(lambda ignore: curs.execute(
            "insert into sitemap_item (sitemap_id,item_id,app) values (%s, %s,%s)",
            (nodeId, itemId, app)
            ))
        d = defer.waitForDeferred(d)
        yield d
        d.getResult()
        yield None


    @requiredPermissions(UPDATE_SITEMAP)
    def removeNode(self, node):
        sql = "select delete_node('sitemap', %s)"
        d = self.storeSession.curs.execute(sql, (node.path,))
        d.addCallback(lambda ignore: self.storeSession.curs.fetchone())
        d.addCallback( lambda r: None )
        return d

    @requiredPermissions(UPDATE_SITEMAP)
    def moveNode(self, node, direction):
        sql = "select move_node('sitemap', %s, %s)"
        d = self.storeSession.curs.execute(sql, (node.path,direction))
        d.addCallback(lambda ignore: self.storeSession.curs.fetchone())
        d.addCallback( lambda r: None )
        return d
    
    @requiredPermissions(UPDATE_SITEMAP)
    def moveNodeByAmount(self, node, amount):
        sql = "select move_node_by('sitemap', %s, %s)"
        d = self.storeSession.curs.execute(sql, (node.path,amount))
        d.addCallback(lambda ignore: self.storeSession.curs.fetchone())
        d.addCallback( lambda r: None )
        return d    

    def _updateNodeContentItem(self, node, app, itemId):
        sql = """
            update sitemap_item set item_id=%s, app=%s
            where sitemap_id=%s
            """
        return self.storeSession.curs.execute(sql, (itemId, app, node.id))

    def _updateNodeName(self, node, name):
        d = self.storeSession.curs.callproc('rename_node', ('sitemap', node.path, name))
        d.addCallback(lambda spam: self.storeSession.curs.fetchone())
        d.addCallback(lambda spam: self.storeSession.curs.execute("select * from sitemap"))
        return d

    def _updateNodeLevel(self, node, level):
        d = self.storeSession.curs.execute(
            "update sitemap set level=%(level)s where id=%(id)s",
            {'level': level, 'id': node.id}
            )
        return d
    
    def _updateNodeLabel(self, node, label):
        d = self.storeSession.curs.execute(
            "update sitemap set label=%(level)s where id=%(id)s",
            {'level': label, 'id': node.id}
            )
        return d    

