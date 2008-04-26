import pkg_resources
from nevow import tags as T, util
from pollen.nevow import tree
from formal import iformal as iforms
from formal.util import keytocssid
from zope.interface import Attribute



class ITreeNode(tree.INode):
    value = Attribute( 'value' )
    label = Attribute( 'label' )

    
class RadioTreeChoice(object):
    
    tree = None
    blankValue = ''
    blankLabel = ''
    nodeInterface = ITreeNode
    
    def __init__(self, original, tree=None, blankValue=None, blankLabel=None, nodeInterface=None):
        super(RadioTreeChoice,self).__init__(original)
        self.original = original
        if tree is not None:
            self.tree = tree
        if blankValue is not None:
            self.blankValue = blankValue
        if blankLabel is not None:
            self.blankLabel = blankLabel
        if nodeInterface is not None:
            self.nodeInterface = nodeInterface
    
    def render(self, ctx, key, args, errors):

        if errors:
            value = args.get(key,[None])[0]
        else:
            if args is not None:
                value = iforms.IStringConvertible(self.original).fromType(args.get(key))
            
        def render_node(ctx, data):
            tag = ctx.tag
            data = self.nodeInterface(data)
            tag.fillSlots('value',data.value)
            tag.fillSlots('label',data.label)
            if str(data.value) == str(value):
                tag = tag(checked='checked')
            return tag

        template = T.div()[
            T.input( pattern='item', render=render_node, type='radio', name=key, value=T.slot('value') )[
                T.slot('label')
                ],
            T.input( pattern='itemdisabled', render=render_node, disabled="disabled", type='radio', name=key, value=T.slot('value') )[
                T.slot('label')
                ]
            ]

        return T.invisible(data=self.tree, render=tree.render)[template]
    
    def processInput(self, ctx, key, args):
        value = args.get(key, [''])[0].decode(util.getPOSTCharset(ctx))
        value = iforms.IStringConvertible(self.original).toType(value)
        return self.original.validate(value)

