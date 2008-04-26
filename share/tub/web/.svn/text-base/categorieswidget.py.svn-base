from twisted.internet import defer
from twisted.python import components
from nevow import tags as T, util as nevowutil, rend, accessors, inevow
from pollen.nevow import tree
from formal import iformal as iforms

from tub.web import util, xforms


class FacetData( object ):
    pass

components.registerAdapter( accessors.ObjectContainer, FacetData, inevow.IContainer )

class CheckboxTreeMultichoice(object):
    """
        Render all the Facets in a single widget.
        The individual categories can be selected using checkboxes.
        Currently the data is stored as a sequence this could be changed to use a
        dictionary.
    """
    
    tree = None
    blankValue = ''
    blankLabel = ''
    nodeInterface = xforms.ITreeNode
    
    def __init__(self, original):
        super(CheckboxTreeMultichoice,self).__init__(original)
        self.original = original
    
    def _render(self, ctx, key, args, errors, value, tag):

        def data_facets( ctx, data ):

            storeSession = util.getStoreSession(ctx)
            avatar = util.getAvatar(ctx)

            @defer.deferredGenerator
            def loadCategories(facets):
                d = defer.waitForDeferred(avatar.getCategoryManager(storeSession))
                yield d
                categories = d.getResult()
                rv = []
                for f in facets:
                    facetData = FacetData()
                    facetData.label = f[2]
                    facetData.textid = f[1]
                    rv.append( facetData )
                    d = defer.waitForDeferred(categories.loadCategories(facetData.textid))
                    yield d
                    facetData.tree = d.getResult().children
                yield rv

            d = avatar.getCategoryManager(storeSession)
            d.addCallback(lambda categories: categories.loadFacets())
            d.addCallback(loadCategories)
            return d
            
        def render_facet( ctx, data):
            tag = ctx.tag
            tag.fillSlots('facetlabel',data.label)
            return tag

        def render_node( ctx, data ):
            tag = ctx.tag
            tag.fillSlots( 'value', data.path )
            tag.fillSlots( 'label', data.label )
            if data.path in value:
                tag.children[0] = tag.children[0](checked='checked')
            else:
                tag.children[0](checked=None)
            return tag
            
        template = T.div(class_='categorieswidget')[
            T.ul( data=data_facets, render=rend.sequence)[
                T.li( pattern="item", render=render_facet )[
                    T.slot( 'facetlabel' ),
                    
                    T.div( data=T.directive( 'tree' ), render=tree.render )[
                        T.invisible( pattern='item', render=render_node ) [
                            tag,
                            T.slot( 'label' )
                        ]
                    ],
                ]
            ]
        ]

        return T.invisible()[template]

    def render(self, ctx, key, args, errors):
        if errors:
            value = args.get(key,[None])
        else:
            if args is not None:
                value = iforms.ISequenceConvertible(self.original).fromType(args.get(key))
                if value is None:
                    value = [None]
        tag = T.input( type='checkbox', name=key, value=T.slot( 'value' ) )
        return self._render(ctx, key, args, errors, value, tag)

    def renderImmutable(self, ctx, key, args, errors):
        if args is not None:
            value = iforms.ISequenceConvertible(self.original).fromType(args.get(key))
            if value is None:
                value = [None]
        tag = T.input( type='checkbox', class_='disabled', disabled='disabled', name=key, value=T.slot( 'value' ) )
        return self._render(ctx, key, args, errors, value, tag)
    
    def processInput(self, ctx, key, args):
        values = args.get(key, [''])
        decodedValues = []
        for value in values:
            value = value.decode(nevowutil.getPOSTCharset(ctx))
            decodedValues.append( value )
        decodedValues = iforms.ISequenceConvertible(self.original).toType(decodedValues)
        return self.original.validate( decodedValues )

try:
    from formal import iformal
    class FormalCheckboxTreeMultichoice(object):

        """
            Render all the Facets in a single widget.
            The individual categories can be selected using checkboxes.
            Currently the data is stored as a sequence this could be changed to use a
            dictionary.
        """
        
        tree = None
        blankValue = ''
        blankLabel = ''
        nodeInterface = xforms.ITreeNode
        
        def __init__(self, original):
            super(FormalCheckboxTreeMultichoice,self).__init__(original)
            self.original = original
        
        def _render(self, ctx, key, args, errors, value, tag):

            def data_facets( ctx, data ):

                storeSession = util.getStoreSession(ctx)
                avatar = util.getAvatar(ctx)

                @defer.deferredGenerator
                def loadCategories(facets):
                    d = defer.waitForDeferred(avatar.getCategoryManager(storeSession))
                    yield d
                    categories = d.getResult()
                    rv = []
                    for f in facets:
                        facetData = FacetData()
                        facetData.label = f[2]
                        facetData.textid = f[1]
                        rv.append( facetData )
                        d = defer.waitForDeferred(categories.loadCategories(facetData.textid))
                        yield d
                        facetData.tree = d.getResult().children
                    yield rv

                d = avatar.getCategoryManager(storeSession)
                d.addCallback(lambda categories: categories.loadFacets())
                d.addCallback(loadCategories)
                return d
                
            def render_facet( ctx, data):
                tag = ctx.tag
                tag.fillSlots('facetlabel',data.label)
                return tag

            def render_node( ctx, data ):
                tag = ctx.tag
                tag.fillSlots( 'value', data.path )
                tag.fillSlots( 'label', data.label )
                if data.path in value:
                    tag.children[0] = tag.children[0](checked='checked')
                else:
                    tag.children[0](checked=None)
                return tag
                
            template = T.div(class_='categorieswidget')[
                T.p(class_="opener")['click to open/close'],
                T.ul( class_='panel', data=data_facets, render=rend.sequence)[
                    T.li( pattern="item", render=render_facet )[
                        T.slot( 'facetlabel' ),
                        
                        T.div( data=T.directive( 'tree' ), render=tree.render )[
                            T.invisible( pattern='item', render=render_node ) [
                                tag,
                                T.slot( 'label' )
                            ]
                        ],
                    ]
                ]
            ]

            return T.invisible()[template]

        def render(self, ctx, key, args, errors):
            if errors:
                value = args.get(key,[None])
            else:
                if args is not None:
                    value = iformal.ISequenceConvertible(self.original).fromType(args.get(key))
                    if value is None:
                        value = [None]
            tag = T.input( type='checkbox', name=key, value=T.slot( 'value' ) )
            return self._render(ctx, key, args, errors, value, tag)

        def renderImmutable(self, ctx, key, args, errors):
            if args is not None:
                value = iformal.ISequenceConvertible(self.original).fromType(args.get(key))
                if value is None:
                    value = [None]
            tag = T.input( type='checkbox', class_='disabled', disabled='disabled', name=key, value=T.slot( 'value' ) )
            return self._render(ctx, key, args, errors, value, tag)
        
        def processInput(self, ctx, key, args):
            values = args.get(key, [''])
            decodedValues = []
            for value in values:
                value = value.decode(nevowutil.getPOSTCharset(ctx))
                decodedValues.append( value )
            decodedValues = iformal.ISequenceConvertible(self.original).toType(decodedValues)
            return self.original.validate( decodedValues )
except ImportError:
    print '*** Formal not found, Formal widgets not available ***'

