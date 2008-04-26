class Node:
    """
    A node class to represent a hierarchy node.
    Run with --output to show types of output.
    Run with --unit to show unit tests
    Run with --cache "test1, test2" or --cache all to cache new unit tests
    """

    def __init__(self, node_tree, node, obj):
        "Set up a node"
        self.node_tree = node_tree
        self.id = node['id']
        self.obj_id = node['obj_id']
        self.group_id = node['group_id']
        self.lft_node = node['lft_node']
        self.rgt_node = node['rgt_node']
        self.parent_id = node['parent']
        self.obj = obj

    def _get_children(self):
        # Delegate to node tree
        return self.node_tree.find_children_of_node(self)

    def _get_parent(self):
        # Delegate to node tree
        return self.node_tree.find_parent_of_node(self)

    def _get_descendants(self):
        # Delegate to node tree
        return self.node_tree.find_descendants_of_node(self)
    
    def _get_path_to_root(self):
        # Delegate to node tree
        return self.node_tree.find_path_to_root(self)

    # These are defined as attributes but are actually methods... v. cool technique
    parent = property(_get_parent)
    children = property(_get_children)
    descendants = property(_get_descendants)
    path_to_root = property(_get_path_to_root)
    
    
    def is_parent_of(self, node):
        return node.parent_id == self.id

    def is_child_of(self, node):
        return self.parent_id == node.id

    def __repr__(self):
        "Print method"
        return 'Node{id=%r, lft_node=%r, rgt_node=%r, parent_id=%r, obj_id=%r, obj=%r}' % (self.id, self.lft_node, self.rgt_node, self.parent_id, self.obj_id, self.obj)

    def __eq__(self, other):
        "An equals method for nodes"
        id = (self.id == other.id)
        group_id = (self.group_id == other.group_id)
        lft_node = (self.lft_node == other.lft_node)
        rgt_node = (self.rgt_node == other.rgt_node)
        parent_id = (self.parent_id == other.parent_id)
        result = (id & group_id & lft_node & rgt_node & parent_id)
        return result

    def __cmp__(self, other):
        if self.lft_node > other.lft_node:
            return 1
        elif self.lft_node < other.lft_node:
            return -1
        else:
            return 0
    
    # Strangely, AssertEquals uses the equals method for lists but not equals for 
    # single values. Hence we need a not equals too.
    def __ne__(self, other):
        "A not equals method - Not __eq__"
        return not (self == other)
    
    # Used to limit what gets stored in a pickle (shelve)
    def __getstate__(self):
        return {'id':self.id, 'group_id':self.group_id, 'lft_node':self.lft_node, 'rgt_node':self.rgt_node, 'parent_id':self.parent_id, 'obj':self.obj}

class NodeTree:
    "A tree class to represent a hierarchy of nodes"

    def __init__(self, node_data, objs):
        """Build a tree from a list of nested set data and a list of objects.

        node_data: list of (id,object,group_id,lft_node,rgt_node,parent) tuples.
        objs: list of (id,object) tuples
        """
        # Read data in and converts to dictionaries
        self._node_data = {}
        for node in node_data:
            item = dict(zip(('id', 'obj_id', 'group_id', 'lft_node', 'rgt_node', 'parent'), node))
            self._node_data[item['id']] = item
        self._node_objs = {}
        for obj in objs:
            self._node_objs[obj[0]] = obj[1]
        # Builds the nodes
        self._build_node_objects()
        # Initialises a nested list representation of the nodes
        self._build_nested_childen_by_node()
        # Assign the root node
        self.root_node = self.find_root_node()

    def _build_node_objects(self):
        self._node_objects = {}
        for id, node in self._node_data.items():
            self._node_objects[id] = \
                Node(self, node, self._node_objs[node['obj_id']])

    def _build_nested_childen_by_node(self):
        self.nested_children_by_node = {}
        for id, node in self._node_data.items():
            # Find myself in nested_children_by_node, creating an empty dict
            # if I don't exist yet
            myself = self.nested_children_by_node.setdefault(id, {})
            # Register a reference to myself with parent
            if node['parent']:
                # Find my parent in nested_children_by_node, creating an
                # empty dict if the parent doesn't exist
                parent = self.nested_children_by_node.setdefault(   
                     node['parent'], {})
                # Add a reference to myself to the parent's dictionary
                parent[id] = myself

    def find_node_by_id(self, id):
        return self._node_objects[int(id)]

    def find_node_by_obj_id(self, obj_id):
        for node in self._node_objects.values():
            if node.obj_id == obj_id:
                return node
        return None

    def find_parent_of_node(self, node):
        return self._node_objects[node.parent_id]

    def find_children_of_node(self, node):
        descendants = self.nested_children_by_node[node.id]
        result = [self._node_objects[child] for child in descendants.keys()]
        result.sort()
        return result

    def find_descendants_of_node(self, node):
        descendants = self.nested_children_by_node[node.id]
        result = [self._node_objects[child] for child in flatten(descendants)]
        result.sort()
        return result

    def find_root_node(self):
        node_ids = self._node_objects.keys()
        for id, node in self._node_objects.items():
            if node.parent_id not in node_ids:
                return node
        
    def find_path_to_root(self, node):
        # Loop from current node back to root building a reverse
        # ordered list (ie root first)
        path_to_root = []
        path_to_root.insert(0,node)
        while node != self.root_node:
            node = node.parent
            path_to_root.insert(0, node)
            
        return path_to_root
            
        

def flatten(dict_to_flatten, result=None):
    # Used to flatten a nested list into a list
    if result is None: result = []
    for key, value in dict_to_flatten.items():
        result.append(key)
        if value: flatten(value, result)
    return result


#------------------------------- Testing ---------------------------------------
def process(unit, cache, output):
    "Process Tests"
    # Set up test data
    data = [
        [1,'flavour','flavour',1,14,0],
        [2,'sweet','flavour',2,5,1],
        [3,'sugar','flavour',3,4,2],
        [4,'sour','flavour',6,13,1],
        [5,'lemon','flavour',7,8,4],
        [6,'lime','flavour',9,12,4],
        [7,'limejuice','flavour',10,11,6]
        ]
    names = [
        ['flavour','flavour'],
        ['sweet','sweet'],
        ['sugar','sugar'],
        ['sour','sour'],
        ['lemon','lemon'],
        ['lime','lime'],
        [ 'limejuice','lime juice']
        ]

    # Setup
    tree = NodeTree(data,names)
    
    # Initialise result
    result = {}
    # Get a node by Id
    result['node'] = tree.find_node_by_id(4)

    # Nodes Parent
    result['node_parent'] = result['node'].parent

    # Nodes Children
    result['node_children'] = result['node'].children

    # Nodes Descendants
    result['node_descendants'] = result['node'].descendants

    # Get descendants of root
    result['root_node_descendants'] = tree.find_node_by_id(1).descendants

    # is_parent_of
    result['is_parent_of'] = result['node'].parent.is_parent_of(result['node'])
    
    # is_child_of
    result['is_child_of'] = result['node'].is_child_of(result['node'].parent)

    # root node
    result['root_node'] = tree.root_node

    # path to root
    node = tree.find_node_by_id(7)
    result['path_to_root'] = node.path_to_root

    import shelve
    dbase = shelve.open('nodes.cache')

    if output:
        print '\n\nPrinting Tests\n============\n'
        
        for key, value in result.items():
            print '\n  %s\n  ----' % (key)
            print '  ' + str(value)
        
    if cache:
        print '\n\nLatching Results \n================\n'

        for key, value in result.items():
            for item in cache:
                if item in ('all', key):
                    print '  processing %s' % (key)
                    dbase[key] = value
        
    if unit:
        print '\n\nUnit Testing\n============\n'
        import unittest
        class NodeTreeTestCase(unittest.TestCase):
            
            def setUp(self):
                self.tree = NodeTree(data, names)
                
            def test_find_node_by_id(self):
                ids = [item[0] for item in data]
                for id in ids:
                    self.failIf(not self.tree.find_node_by_id(id))

            def test_check_against_cache(self):
                for key in dbase.keys():
                    self.assertEqual(dbase[key], result[key])

        NodeTreeTestSuite = unittest.TestSuite()
        NodeTreeTestSuite.addTest(NodeTreeTestCase("test_find_node_by_id"))
        NodeTreeTestSuite.addTest(NodeTreeTestCase("test_check_against_cache"))

        runner = unittest.TextTestRunner()
        runner.run(NodeTreeTestSuite)
         
    dbase.close()


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

# Read Options if called command line
import sys
import getopt
import string

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            # First list is short options (options with arguments followed by ':')
            # second is long options (options with arguments followed by '=')
            opts, args = getopt.getopt(argv[1:], "huc:o", ["help","unit","cache=","output"])
        except getopt.error, msg:
             raise Usage(msg)
        # option processing
        unit = False
        output = False
        cache = None
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(__doc__)
            if option in ("-u", "--unit"):
                unit = True
            if option in ("-c", "--cache"):
                cache = string.split(value,',')
            if option in ("-o", "--output"):
                output = True
        # Run process
        process(unit, cache, output)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())
