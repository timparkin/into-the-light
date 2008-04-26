"""
Extension of PySyck that treats all scalars (implicit typing is switched off)
as UTF-8 encoded strings.

To convert scalars to specific types use the standard YAML syntax, i.e.
"!int 1".
"""

import syck



class Loader(syck.Loader):


    def construct(self, node):
        # Implicit typing is always disabled but we want unicode instances, not
        # byte streams, where possible. So, if the node is a scalar and it's
        # not been explicitly given a type then treat it as a utf-8 encoded
        # string.
        if node.kind == 'scalar' and node.tag is None:
            return super(Loader, self).construct_python_unicode(node)
        return super(Loader, self).construct(node)



def load(source, Loader=Loader):
    return syck.load(source, Loader=Loader, implicit_typing=False)



if __name__ == '__main__':

    import unittest

    POUND = u'\xa3'
    POUND_ENC = POUND.encode('utf-8')

    class TestCase(unittest.TestCase):

        def test_strings(self):
            s = load("- foo\n- %s\n- !string %s" % (POUND_ENC, POUND_ENC))
            self.assertEquals(s, [u'foo', POUND, POUND_ENC])
            self.assertEquals(map(type, s), [unicode, unicode, str])

        def test_likeNumbers(self):
            s = load("- 1\n- 1.2")
            self.assertEquals(s, [u'1', u'1.2'])

        def test_explicitNumbers(self):
            s = load("- !int 1\n- !float 1.2")
            self.assertEquals(s, [1, 1.2])
            self.assertEquals(map(type, s), [int, float])


    unittest.main()

