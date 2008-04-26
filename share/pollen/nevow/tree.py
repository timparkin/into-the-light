from nevow import compy as components, tags as T, inevow, stan
from pollen.hierarchy import nodes
from zope.interface import Attribute


# Create and Register Adapter for Dict to Node and Node to Node
class INode(components.Interface):
    children = Attribute( 'children' )
    
class DictNode(components.Adapter):
    children = property(lambda self: self.original.get('children',None))
    
components.registerAdapter(DictNode, dict, INode)

class HierarchyNode(components.Adapter):
    children = property(lambda self: self.original.children)
    
components.registerAdapter(HierarchyNode, nodes.Node, INode)


# node renderer function returning stan tags
def render(ctx, data):

    def render_children(ctx, data):
        yield [T.invisible(data=child, render=render_node) for child in data ]        

    def render_node(ctx, data):
        tag = T.li[item()]
        children = INode(data).children
        if children:
            tag[T.ul[render_children(ctx, children)]]
        return tag
            
    item = inevow.IQ(ctx).patternGenerator('item')
    try:
        itemdisabled = inevow.IQ(ctx).patternGenerator('itemdisabled')
    except stan.NodeNotFound:
        itemdisabled = item
        
    tag = T.ul()
    if isinstance(data, (tuple,list)):
        tag = tag[render_children]
    else:
        tag = tag[render_node]
        
    return tag

