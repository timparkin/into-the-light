"""
Rich text widget.
Initially support entering reST, but in the furture HTML, plain text ...
"""

from zope.interface import implements
from twisted.python.components import registerAdapter
from nevow import tags as T, rend, inevow, loaders, util
import formal as forms
from formal.util import keytocssid
from formal.form import widgetResourceURLFromContext
from formal import types, iformal as iforms, ReSTTextArea, converters

import restsupport
from cms.widgets.itemselection import encodeTypes

class RichTextData(object):
    """Type for holding rich text data, the type attribute
       identifies the type of data held in the content
       attribute"""
    REST = 'reST'
    def __init__(self, type=None, content=None):
        self.type = type or self.REST
        self.content = content

    def htmlFragment(self, restWriter=None):
        if not self.content:
            return ''
        if self.type == self.REST:
            return restsupport.htmlFragment(self.content, writer=restWriter)

class RichText(types.Type):
    """Forms type used for rich text"""

    def __init__(self, **kwds):
        strip = kwds.pop('strip', None)
        super(RichText, self).__init__(**kwds)
        self.strip = strip or False
        

    def validate(self, value):
        # For the moment all the validation is against the content

        if self.strip and value.content is not None:
            value.content = value.content.strip()
        if not value.content:
            value.content = None

        value.content = super(RichText, self).validate(value.content)
        return value

class IRichTextConvertible(iforms.IConvertible):
    pass


class RichTextArea(object):
    implements(iforms.IWidget)

    def _namer(self, prefix):
        def _(part):
            return '%s__%s'%(prefix, part)
        return _

    def __init__(self, original, cols=None, rows=None, restWriter=None, withImagePicker=False, withItemSelection=False,
            itemSelectionTypes=None, itemSelectionTemplates=None):
        self.original = original
        self.cols = cols or 48
        self.rows = rows or 6
        self.restWriter=restWriter
        self.withImagePicker=withImagePicker

        self.withItemSelection=withItemSelection
        self.itemSelectionTemplates=itemSelectionTemplates
        self.itemSelectionTypes=itemSelectionTypes

    def _renderTag(self, ctx, type, content, key, readonly):
        namer = self._namer(key)

        rta = ReSTTextArea(None)
        
        typeTag = T.input(type='hidden', name=namer('type'), value=type)
        contentTag = self._renderReSTTag(ctx, content, key, readonly)

        return (typeTag, contentTag)

    def render(self, ctx, key, args, errors):
        namer = self._namer(key)
        if errors:
            type = args.get(namer('type'), [''])[0]
            content = args.get(namer('content'), [''])[0]
        else:
            converter = IRichTextConvertible(self.original)
            tmp = converter.fromType(args.get(key))
            if tmp:
                type = tmp.type
                content = tmp.content
            else:
                type = RichTextData.REST
                content = None
        return self._renderTag(ctx, type, content, key, False)

    def renderImmutable(self, ctx, key, args, errors):
        converter = IRichTextConvertible(self.original)
        tmp = converter.fromType(args.get(key))
        if tmp:
            type = tmp.type
            content = tmp.content
        else:
            type = RichTextData.REST
            content = ''
        return self._renderTag(ctx, type, content, key, True)

    def processInput(self, ctx, key, args):
        namer = self._namer(key)
        type = args.get(namer('type'), [''])[0].decode(util.getPOSTCharset(ctx))
        content = args.get(namer('content'), [''])[0].decode(util.getPOSTCharset(ctx))

        value = IRichTextConvertible(self.original).toType(RichTextData(type, content))
        return self.original.validate(value)

    def getResource(self, ctx, key, segments):
        return RichTextReSTPreview(ctx, self.restWriter, key, segments[0]), segments[1:]

    def _renderReSTTag(self, ctx, content, key, readonly):
        namer = self._namer(key)

        tag=T.invisible()
        ta=T.textarea(name=namer('content'), id=keytocssid(namer('content')), cols=self.cols, rows=self.rows)[content or '']
        if readonly:
            ta(class_='readonly', readonly='readonly')
        tag[ta]

        if not readonly:
            try:
                import docutils
            except ImportError:
                raise
            else:
                form = iforms.IForm( ctx )
                srcId = keytocssid(namer('content'))
                previewDiv = srcId + ['-preview-div']
                frameId = srcId + ['-preview-frame']
                targetURL = widgetResourceURLFromContext(ctx, form.name).child(key).child( srcId )
                tag[T.br()]
                tag[T.button(onClick=["return Forms.Util.previewShow('",previewDiv,"', '",frameId,"', '",targetURL,"');"] )['Preview ...']]
                if self.withImagePicker:
                    tag[T.button(onclick=["return Cms.Forms.ImagePicker.popup('",srcId,"','tag')"])['Choose image ...']]

                if self.withItemSelection:
                    if self.itemSelectionTemplates:
                        itemSelectionTemplates = ','.join(self.itemSelectionTemplates)
                    else:
                        itemSelectionTemplates = ''
                    if self.itemSelectionTypes:
                        itemSelectionTypes = encodeTypes(self.itemSelectionTypes)
                    else:
                        itemSelectionTypes = ''
                    tag[T.button(onclick=["return Cms.Forms.ItemSelection.popupForReST('",srcId,"', '",itemSelectionTypes,"', 'rest')"])['Choose items ...']]

                tag[T.div(id=previewDiv, class_="preview-hidden")[
                        T.iframe(class_="preview-frame", name=frameId, id=frameId),
                        T.br(),
                        T.button(onClick="return Forms.Util.previewHide('%s');"%(previewDiv))['Close']
                    ]
                ]

        return tag

class RichTextReSTPreview(rend.Page):

    def __init__(self, ctx, restWriter, key, srcId):
        self.restWriter = restWriter

        form = iforms.IForm( ctx )
        u = widgetResourceURLFromContext(ctx, form.name).child(key).child( srcId ).child('_submit')
        self.destId=srcId + '-dest'
        formId=srcId + '-form'

        stan = T.html()[
            T.head()[
                T.script(type="text/javascript")["""
                function ReSTTranslate() {
                    dest = document.getElementById('%(destId)s');
                    form = document.getElementById('%(formId)s');
                    src = parent.document.getElementById('%(srcId)s');
                    dest.value = src.value;
                    form.submit();
                }

                """%{'srcId':srcId, 'destId':self.destId, 'formId':formId}]
            ],
            T.body()[
                T.form(id=formId, method="POST", action=u)[
                    T.input(type="hidden", name=self.destId, id=self.destId)
                ],
                T.script(type="text/javascript")["ReSTTranslate();"],
            ],
        ]

        self.docFactory = loaders.stan(stan)

    def child__submit(self, ctx):
        args = inevow.IRequest(ctx).args
        value = args.get(self.destId, [''])[0]

        from docutils.utils import SystemMessage

        try:
            if self.restWriter:
                restValue = self._html_fragment(value, writer=self.restWriter)
            else:
                restValue = self._html_fragment(value, writer_name='html')
        except SystemMessage, e:
            restValue = str(e)

        try:
            # Check whether it is valid to be loaded
            xml = """<!DOCTYPE html
                    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
                    <div xmlns:n="http://nevow.com/ns/nevow/0.1" >""" + restValue + '</div>'

            test = loaders.xmlstr(xml, ignoreDocType=True).load() 
        except Exception, e:
            restValue = "HTML Validation Error: please check any raw HTML blocks."

        stan = T.html()[
            T.head()[
                T.style(type="text/css")["""

                    .system-message {border: 1px solid red; background-color: #FFFFDD; margin: 5px; padding: 5px;}
                    .system-message-title { font-weight: bold;}
                """
                ]
            ],
            T.body()[
                T.div()[
                    T.xml(restValue)
                ]
            ],
        ]

        self.docFactory = loaders.stan(stan)

        return self

    def _html_fragment(self, input_string, writer=None, writer_name=None):
        return restsupport.htmlFragment(input_string, writer=writer, writer_name=writer_name)

registerAdapter(converters.NullConverter, RichText, IRichTextConvertible)
registerAdapter(RichTextArea, RichText, iforms.IWidget)


try:
    from formal import iformal, types as formal_types, converters as formal_converters, ReSTTextArea as formal_ReSTTextArea

    from formal.util import keytocssid as formal_keytocssid
    from formal.form import widgetResourceURLFromContext as formal_widgetResourceURLFromContext

    class FormalRichText(formal_types.Type):
        """Forms type used for rich text"""

        def __init__(self, **kwds):
            strip = kwds.pop('strip', None)
            super(FormalRichText, self).__init__(**kwds)
            self.strip = strip or False
            

        def validate(self, value):
            # For the moment all the validation is against the content

            if self.strip and value.content is not None:
                value.content = value.content.strip()
            if not value.content:
                value.content = None

            value.content = super(FormalRichText, self).validate(value.content)
            return value

    class IFormalRichTextConvertible(iformal.IConvertible):
        pass

    class FormalRichTextArea(object):
        implements(iformal.IWidget)

        def _namer(self, prefix):
            def _(part):
                return '%s__%s'%(prefix, part)
            return _

        def __init__(self, original, cols=None, rows=None, restWriter=None, withImagePicker=False):
            self.original = original
            self.cols = cols or 48
            self.rows = rows or 6
            self.restWriter=restWriter
            self.withImagePicker=withImagePicker

        def _renderTag(self, ctx, type, content, key, readonly):
            namer = self._namer(key)

            rta = formal_ReSTTextArea(None)
            
            typeTag = T.input(type='hidden', name=namer('type'), value=type)
            contentTag = self._renderReSTTag(ctx, content, key, readonly)

            return (typeTag, contentTag)

        def render(self, ctx, key, args, errors):
            namer = self._namer(key)
            if errors:
                type = args.get(namer('type'), [''])[0]
                content = args.get(namer('content'), [''])[0]
            else:
                converter = IFormalRichTextConvertible(self.original)
                tmp = converter.fromType(args.get(key))
                if tmp:
                    type = tmp.type
                    content = tmp.content
                else:
                    type = RichTextData.REST
                    content = None
            return self._renderTag(ctx, type, content, key, False)

        def renderImmutable(self, ctx, key, args, errors):
            converter = IFormalRichTextConvertible(self.original)
            tmp = converter.fromType(args.get(key))
            if tmp:
                type = tmp.type
                content = tmp.content
            else:
                type = formal_RichTextData.REST
                content = ''
            return self._renderTag(ctx, type, content, key, True)

        def processInput(self, ctx, key, args):
            namer = self._namer(key)
            type = args.get(namer('type'), [''])[0].decode(util.getPOSTCharset(ctx))
            content = args.get(namer('content'), [''])[0].decode(util.getPOSTCharset(ctx))

            value = IFormalRichTextConvertible(self.original).toType(RichTextData(type, content))
            return self.original.validate(value)

        def getResource(self, ctx, key, segments):
            return FormalRichTextReSTPreview(ctx, self.restWriter, key, segments[0]), segments[1:]

        def _renderReSTTag(self, ctx, content, key, readonly):
            namer = self._namer(key)

            tag=T.invisible()
            ta=T.textarea(name=namer('content'), id=formal_keytocssid(namer('content')), cols=self.cols, rows=self.rows)[content or '']
            if readonly:
                ta(class_='readonly', readonly='readonly')
            tag[ta]

            if not readonly:
                try:
                    import docutils
                except ImportError:
                    raise
                else:
                    form = iformal.IForm( ctx )
                    srcId = formal_keytocssid(namer('content'))
                    previewDiv = srcId + '-preview-div'
                    frameId = srcId + '-preview-frame'
                    targetURL = formal_widgetResourceURLFromContext(ctx, form.name).child(key).child( srcId )
                    tag[T.br()]
                    tag[T.button(onClick="return Forms.Util.previewShow('%s', '%s', '%s');"%(previewDiv, frameId, targetURL))['Preview ...']]
                    if self.withImagePicker:
                        tag[T.button(onclick=["return Cms.Forms.ImagePicker.popup('",srcId,"','tag')"])['Choose image ...']]

                    tag[T.div(id=previewDiv, class_="preview-hidden")[
                            T.iframe(class_="preview-frame", name=frameId, id=frameId),
                            T.br(),
                            T.button(onClick=["return Forms.Util.previewHide('",previewDiv,"');"])['Close']
                        ]
                    ]

            return tag

    class FormalRichTextReSTPreview(rend.Page):

        def __init__(self, ctx, restWriter, key, srcId):
            self.restWriter = restWriter

            form = iformal.IForm( ctx )
            u = formal_widgetResourceURLFromContext(ctx, form.name).child(key).child( srcId ).child('_submit')
            self.destId=srcId + '-dest'
            formId=srcId + '-form'

            stan = T.html()[
                T.head()[
                    T.script(type="text/javascript")["""
                    function ReSTTranslate() {
                        dest = document.getElementById('%(destId)s');
                        form = document.getElementById('%(formId)s');
                        src = parent.document.getElementById('%(srcId)s');
                        dest.value = src.value;
                        form.submit();
                    }

                    """%{'srcId':srcId, 'destId':self.destId, 'formId':formId}]
                ],
                T.body()[
                    T.form(id=formId, method="POST", action=u)[
                        T.input(type="hidden", name=self.destId, id=self.destId)
                    ],
                    T.script(type="text/javascript")["ReSTTranslate();"],
                ],
            ]

            self.docFactory = loaders.stan(stan)

        def child__submit(self, ctx):
            args = inevow.IRequest(ctx).args
            value = args.get(self.destId, [''])[0]

            from docutils.utils import SystemMessage

            try:
                if self.restWriter:
                    restValue = self._html_fragment(value, writer=self.restWriter)
                else:
                    restValue = self._html_fragment(value, writer_name='html')
            except SystemMessage, e:
                restValue = str(e)

            stan = T.html()[
                T.head()[
                    T.style(type="text/css")["""

                        .system-message {border: 1px solid red; background-color: #FFFFDD; margin: 5px; padding: 5px;}
                        .system-message-title { font-weight: bold;}
                    """
                    ]
                ],
                T.body()[
                    T.div()[
                        T.xml(restValue)
                    ]
                ],
            ]

            self.docFactory = loaders.stan(stan)

            return self

        def _html_fragment(self, input_string, writer=None, writer_name=None):
            return restsupport.htmlFragment(input_string, writer=writer, writer_name=writer_name)

    registerAdapter(formal_converters.NullConverter, FormalRichText, IFormalRichTextConvertible)
    registerAdapter(FormalRichTextArea, FormalRichText, iformal.IWidget)
except ImportError:
    print '*** Formal not found, FormalRichText is not available ***'

