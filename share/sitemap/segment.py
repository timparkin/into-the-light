import re
from twisted.python import components
from tub.web.xformal import converters, iformal as iforms, types, validation

class Segment(types.String):
    """Subclass the forms's String type for strings suitable for use as
    URL (and ltree) segments.

    I think this should really be a String with a validator. Or perhaps, the
    String type should have a regex match facility built-in since this is
    quite a common requirement.
    """
    def __init__( self, *a, **kw ):
        self.message = kw.pop( 'message', None )
        super(Segment, self).__init__(*a, **kw)

    pattern = '^[_a-zA-Z0-9]*$'
    strip = True
    def validate(self, value):
        value = super(Segment, self).validate(value)
        if value is not None:
            if not re.match(self.pattern, value):
                raise validation.FieldValidationError(self.message)
        return value

components.registerAdapter(converters.NullConverter, Segment, iforms.IStringConvertible)
