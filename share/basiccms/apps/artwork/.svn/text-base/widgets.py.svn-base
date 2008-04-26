from zope.interface import implements
from nevow import tags as T
from formal import iformal, validation

class SizeWidget(object):
    implements( iformal.IWidget )

    def __init__(self, original):
        self.original = original

    def _namer(self, prefix):
        def _(part):
            return '%s__%s' % (prefix,part)
        return _

    def _renderTag(self, ctx, height, width, depth, namer, readonly):
        heightTag = T.input(type="text", name=namer('height'), value=height, size=8)
        widthTag = T.input(type="text", name=namer('width'), value=width, size=8)
        depthTag = T.input(type="text", name=namer('depth'), value=depth, size=8)
        if readonly:
            tags = (heightTag, widthTag, depthTag)
            for tag in tags:
                tag(class_='readonly', readonly='readonly')

        return heightTag, 'h ', widthTag, 'w ', depthTag, 'd '


    def render(self, ctx, key, args, errors):
        converter = iformal.ISequenceConvertible(self.original)
        namer = self._namer(key)
        if errors:
            height = args.get(namer('height'), [''])[0]
            width = args.get(namer('width'), [''])[0]
            depth = args.get(namer('depth'), [''])[0]
        else:
            value = args.get(key)
            height, width, depth = None, None, None
            if value:
                height, width, depth = converter.fromType(args.get(key))

        return self._renderTag(ctx, height, width, depth, namer, False)

    def renderImmutable(self, ctx, key, args, errors):
        converter = iformal.ISequenceConvertible(self.original)
        namer = self._namer(key)
        height, width, depth = converter.fromType(args.get(key))
        return self._renderTag(ctx, height, width, depth, namer, True)


    def processInput(self, ctx, key, args):
        namer = self._namer(key)
        # Get the form field values as a (hwd) tuple
        hwd = [args.get(namer(part), [''])[0].strip() for part in ('height', 'width', 'depth')]

        # if anything is entered then both height and width must be entered
        fieldsEntered = len([p for p in hwd if p])
        if fieldsEntered != 0 and fieldsEntered < 2:
            raise validation.FieldValidationError("Invalid size")

        if fieldsEntered != 0 and (not hwd[0] or not hwd[1]):
            raise validation.FieldValidationError("Invalid size")

        if fieldsEntered == 0:
            hwd = None

        hwd = iformal.ISequenceConvertible(self.original).toType(hwd)
        return self.original.validate(hwd)

