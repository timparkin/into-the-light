from pollen.hierarchy import nodes
from nevow import flat, tags as T, rend
from pollen.nevow import tree

def process(unit, cache, output):
    "Process Tests"
        
        
    def dictTree():
        node = [
                {'id':1,'name':'flavour'},
                {'id':2,'name':'sweet'},
                {'id':3,'name':'sugar'},
                {'id':4,'name':'sour'},
                {'id':5,'name':'lemon'},
                {'id':6,'name':'lime'},
                {'id':7,'name':'lime juice'}
               ]
        
        node[0]['children'] = [node[1], node[3]]
        node[1]['children'] = [node[2]]
        node[3]['children'] = [node[4],node[5]]
        node[5]['children'] = [node[6]]
        
        tree = node[0]
        
        return tree

    def nodeTree():
        # Set up Dictionary Data
        data = [
                [1,1,'flavour',1,14,0],
                [2,2,'flavour',2,5,1],
                [3,3,'flavour',3,4,2],
                [4,4,'flavour',6,13,1],
                [5,5,'flavour',7,8,4],
                [6,6,'flavour',9,12,4],
                [7,7,'flavour',10,11,6],
               ]
        names = [ [1,'flavour'], [2,'sweet'], [3,'sugar'], [4,'sour'], [5,'lemon'], [6,'lime'], [ 7,'lime juice'] ] 
    
        # Setup
        tree = nodes.NodeTree(data,names).find_root_node()
        
        return tree
        
    result = {}

    
    # >>>>>>>>>>>>>>>>>  Self Documenting Tests >>>>>>>>>>>>>>>>>>>>
    
    # Build the tree from dict data
    template = T.input( pattern='item', render=rend.mapping, type='radio', name='tree', value=T.slot('id') )[T.slot('name')]

    result['dicttreehtml'] = flat.flatten( T.invisible(data=dictTree(), render=tree.render)[template] )

    
    # Build the tree from node data
    def render_node(ctx, data):
        ctx.fillSlots('obj_id',data.obj_id)
        ctx.fillSlots('obj',data.obj)
        return ctx.tag
    template = T.input( pattern='item', render=render_node, type='radio', name='tree', value=T.slot('obj_id') )[T.slot('obj')]
    
    result['nodetreehtml'] = flat.flatten( T.invisible(data=nodeTree(), render=tree.render)[template] )
    
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # set up the shelve import
    import shelve
    import os
    dbase = shelve.open('%s/treedata/tree.cache' % os.path.dirname(__file__))

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
            
            def test_dict_vs_node_html(self):
                self.assertEqual(result['dicttreehtml'], result['nodetreehtml'])
                    
            def test_check_against_cache(self):
                for key in dbase.keys():
                    self.assertEqual(dbase[key], result[key])

        NodeTreeTestSuite = unittest.TestSuite()
        NodeTreeTestSuite.addTest(NodeTreeTestCase("test_dict_vs_node_html"))
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
    

            

    


            