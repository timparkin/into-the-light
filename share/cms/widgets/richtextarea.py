"""
Rich text area widget.
"""

from nevow import inevow, loaders, rend, tags as T, util
from formal import iformal, widget, types
from formal.widgets import richtextarea
from formal.util import render_cssid
from zope.interface import Interface
from cms.widgets.itemselection import encodeTypes

class RichTextArea(richtextarea.RichTextArea):
    """
    A large text entry area that can be used for different formats of formatted text (rest, html, markdown, texy)
    """
    def __init__(self, original, **kwds):
        itemTypes = kwds.pop('itemTypes', None)
        itemTemplates = kwds.pop('itemTemplates', None)
        super(RichTextArea, self).__init__(original, **kwds)
        self.itemTypes = itemTypes
        self.itemTemplates = itemTemplates

    def _renderTag(self, ctx, tparser, tvalue, namer, readonly):
        tag=T.invisible()
        if len(self.parsers) > 1:
            tp = T.select(name=namer('tparser'),id=render_cssid(namer('tparser')))
            if readonly:
                tp(class_='disabled', disabled='disabled')        
            
            for k,v in self.parsers:
                if k == tparser:
                    tp[T.option(selected='selected',value=k)[ v ]]
                else:
                    tp[T.option(value=k)[ v ]]
        else:
            tp = T.input(type='hidden',name=namer('tparser'),id=render_cssid(namer('tparser')),value=self.parsers[0][0])
        tag[tp]     
               
        if self.itemTypes is not None:
            tag[ T.input(type='hidden',class_="itemTypes",name=namer('itemTypes'),id=render_cssid(namer('itemTypes')),value=encodeTypes(self.itemTypes)) ]
        if self.itemTemplates is not None:
            tag[ T.input(type='hidden',class_="itemTemplates",name=namer('itemTemplates'),id=render_cssid(namer('itemTemplates')),value=','.join(self.itemTemplates)) ]

        ta=T.textarea(name=namer('tvalue'), id=render_cssid(namer('tvalue')), cols=self.cols, rows=self.rows)[tvalue or '']
        if readonly:
            ta(class_='readonly', readonly='readonly')
        tag[ [T.br,ta ]]
        return tag


    def render(self, ctx, key, args, errors):
        namer = self._namer(key)
        if errors:
            tparser = args.get(namer('tparser'), [''])[0]
            tvalue = args.get(namer('tvalue'), [''])[0]
        else:
            value = args.get(key)
            if value is not None:
                tparser = getattr(value,'type',None)
                tvalue = getattr(value,'value','')
            else:
                tparser = None
                tvalue = ''
        
        return self._renderTag(ctx, tparser, tvalue, namer, False)
        
    def renderImmutable(self, ctx, key, args, errors):
        namer = self._namer(key)
        if errors:
            tparser = args.get(namer('tparser'), [''])[0]
            tvalue = args.get(namer('tvalue'), [''])[0]
        else:
            value = args.get(key)
            if value is not None:
                tparser = value.type
                tvalue = getattr(value,'value','')
            else:
                tparser = None
                tvalue = ''
        
        return self._renderTag(ctx, tparser, tvalue, namer, True)
    
    def processInput(self, ctx, key, args):
        namer = self._namer(key)
        value = [args.get(namer(part), [''])[0].strip().decode(util.getPOSTCharset(ctx)) for part in ('tparser', 'tvalue')]
        return self.original.validate(types.RichText(*value))



    


    
