"""
Categorisation.
"""

from twisted.internet import defer

from tub import error, hierarchyutil
from tub.capabilities import CommonPermissions, GroupPermission
from tub.capabilities import requiredPermissions


class Category(object):
    """I represent a category
    """

    def __init__(self, id, path, textid, label, children=None, ord=None):
        self.id = id
        self.path = path
        self.textid = textid
        self.label = label
        if children is not None:
            self.children = children
        else:
            self.children = []
        self.ord = ord

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

    def findChildByTextId(self, textid):
        """Find an immediate child with the specified textid.
        """
        for child in self.children:
            if child.textid == textid:
                return child

    def findChildBySegment(self, childSegment):
        childPath = '.'.join((self.path, childSegment))
        for child in self.children:
            if child.path == childPath:
                return child


CAPABILITY_CATEGORY_MGR_ALIAS = 'tub/categores'


UPDATE_CATEGORIES = GroupPermission(CommonPermissions.UPDATE,
        CAPABILITY_CATEGORY_MGR_ALIAS)


class CategoryManager(object):
    """Category storage implementation.
    """
    alias = CAPABILITY_CATEGORY_MGR_ALIAS
    name = 'categories'
    description = 'Categories Manager'

    def __init__(self, avatar, sess):
        self.avatar = avatar
        self.sess = sess

    def loadFacets(self):
        d = self._fetchFacets()
        return d

    def loadCategories(self, name):
        d = self._fetchCategoryRows(name)
        d.addCallback(self._rowsToTree, name)
        return d

    @requiredPermissions(UPDATE_CATEGORIES)
    def updateNode(self, node, textid, label):
        curs = self.sess.curs
        d = defer.Deferred()
        d.addCallback(lambda ignore: curs.execute("""update categories set
            textid=%s, label=%s where path=%s""", (textid, label, node.path)))
        d.addCallback(lambda ignore: curs.callproc("rename_node", ('categories',
            node.path, textid)))
        def updateMem():
            node.textid = textid
        d.addCallback(lambda r: updateMem())
        d.callback(None)
        return d

    @requiredPermissions(UPDATE_CATEGORIES)
    @defer.deferredGenerator
    def addChildToNode(self, node, textid, label):
        curs = self.sess.curs
        d = defer.waitForDeferred( hierarchyutil.isUniquePath( curs,
            'categories', 'path', node.path, textid ) )
        yield d

        if not d.getResult():
            raise error.NotUniqueError()
        d = curs.callproc('insert_node_under', ('categories', node.path, textid,
            textid, label))
        d = defer.waitForDeferred(d)
        yield d
        d.getResult()
        yield None

    @requiredPermissions(UPDATE_CATEGORIES)
    def removeNode(self, node):
        sql = "select delete_node('categories', %s)"
        d = self.sess.curs.execute(sql, (node.path,))
        d.addCallback(lambda ignore: self.sess.curs.fetchone())
        d.addCallback( lambda r: None )
        return d

    @requiredPermissions(UPDATE_CATEGORIES)
    def moveNode(self, node, direction):
        sql = "select move_node('categories', %s, %s)"
        d = self.sess.curs.execute(sql, (node.path,direction))
        d.addCallback(lambda ignore: self.sess.curs.fetchone())
        d.addCallback( lambda r: None )
        return d

    def _fetchCategoryRows(self, facet):
        sql = """
            select
              id, textid, label, path, nlevel(path) as depth, ord
            from
              categories
            where
              path <@ %s
            order by
              nlevel(path), ord
            """
        curs = self.sess.curs
        d = curs.execute(sql,(facet,))
        d.addCallback(lambda ignore: curs.fetchall())
        return d

    def _fetchFacets(self):
        sql = """
            select
              id, textid, label, path, nlevel(path) as depth, ord
            from
              categories
            where
              nlevel(path) = 1
            order by
              ord
            """
        curs = self.sess.curs
        d = curs.execute(sql)
        d.addCallback(lambda ignore: curs.fetchall())
        return d

    def _rowsToTree(self, rows, facet):

        def parentPath(path):
            return '.'.join(path.split('.')[:-1])

        # Create a dict for tracking the node for a particular path.
        pathToNodeMap = {}

        for row in rows:

            # Unpack the row.
            id, textId, label, path, depth, seq = row

            # Create a node and add it to the map.
            node = Category(id, path, textId, label, ord=seq)
            pathToNodeMap[path] = node

            # If the node should have a parent then find the parent node
            # and add the new node as a child.
            if depth > 1:
                # Find the parent node and add it as a child
                parentNode = pathToNodeMap[parentPath(path)]
                parentNode.children.append(node)

        # Return the "root" node.
        return pathToNodeMap[facet]

