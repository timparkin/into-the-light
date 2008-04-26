import zope.interface as zi
from nevow import tags as T
from formal import iformal as iforms
from formal.util import keytocssid

class ImagePickerWidget(object):
    zi.implements(iforms.IWidget)

    def __init__(self, original):
        self.original = original

    def render(self, ctx, key, args, errors):
        if errors:
            value = args.get(key, [''])[0]
        else:
            value = args.get(key)
            if value is None:
                value = ''

        img = T.invisible()
        if value:
            # TODO: work out how to find '/content' out
            img = T.img(src='/content%s?size=200x200'%value , class_="preview")

        return T.div()[
            img, T.br(),
            T.input(type='text', name=key, id=keytocssid(ctx.key), value=value),
            T.button(onclick=["return Cms.Forms.ImagePicker.popup('",render_cssid(ctx.key),"','url')"])['Choose image ...']
            ]

    def renderImmutable(self, ctx, key, args, errors):
        if errors:
            value = args.get(key, [''])[0]
        else:
            value = args.get(key)
            if value is None:
                value = ''

        previewValue = ''
        if value:
            previewValue='/content%s?size=200x200'%value

        return T.div()[
            T.img(src=previewValue, class_="preview"), T.br(),
            T.input(type='text', class_="readonly", readonly="readonly", name=key, id=keytocssid(ctx.key), value=value),
            ]

    def processInput(self, ctx, key, args):
        value = args.get(key, [None])[0] or None
        return self.original.validate(value)

