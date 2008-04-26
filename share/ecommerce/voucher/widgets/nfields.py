from zope.interface import implements
from nevow import tags as T, util as nevowutil
from formal import iformal

class NFieldWidget(object):
    """
    Widget to capture 'n' fields as a sequence, 
    so it can be used for '3 for 2'
    or '2 for 1'
    """
    implements( iformal.IWidget )

    def __init__(self, original, count, separators=None):
        self.original = original
        self.count = count
        self.separators = separators
        if self.separators is None:
            self.separators = []


    def _namer(self, prefix):
        def _(part):
            return '%s__%s' % (prefix,part)
        return _


    def _renderTag(self, ctx, values, namer, readonly):
        valuesAndSeparators = map(None, values, self.separators)
        tag = []
        for i in range(self.count):
            input = T.input(type="text", name=namer(i), value=valuesAndSeparators[i][0], size=4 )
            if readonly:
                tag(class_='readonly', readonly='readonly')

            tag.append( input )
            separator = valuesAndSeparators[i][1]
            if separator:
                tag.append( ' %s '%separator )
        
        return tag


    def render(self, ctx, key, args, errors):
        namer = self._namer(key)
        if errors:
            values = []
            for i in range(self.count):
                values.append( args.get(namer(i), [''])[0] )
        else:
            values = self._getValuesFromArgs(key, args)

        return self._renderTag(ctx, values, namer, False)


    def renderImmutable(self, ctx, key, args, errors):
        values = self._getValuesFromArgs(key, args)
        namer = self._namer(key)
        return self._renderTag(ctx, values, namer, True)


    def _getValuesFromArgs(self, key, args):
        converter = iformal.ISequenceConvertible(self.original)
        values = converter.fromType(args.get(key))
        if values is None:
            values = [None] * self.count
        return values


    def processInput(self, ctx, key, args):
        namer = self._namer(key)
        values = []
        for i in range(self.count):
            value = args.get(namer(i), [''])[0]
            value = value.decode(nevowutil.getPOSTCharset(ctx))
            values.append( value )

        values = iformal.ISequenceConvertible(self.original).toType(values)
        return self.original.validate( values )

