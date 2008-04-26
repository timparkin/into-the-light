"""
PostgreSQL "ltree" type.
"""


class ltree(object):


    def __init__(self, value):
        """
        Create an ltree instance from a path value. The value should be a
        string containing a path with segments separated by '.', e.g., 'a.b.c'.
        """
        self.path = value.split('.')


    def child(self, *path):
        """
        Return the child of self with the given path.
        """
        path = '.'.join(path)
        return ltree('.'.join([str(self), path]))


    @property
    def depth(self):
        return len(self.path)


    def descendentOf(self, other):
        """
        Test if this instance is a descendent of other.
        """
        return self.path[:other.depth] == other.path and \
                self.depth > other.depth


    def childOf(self, other):
        """
        Test if this instance is a child (i.e. an immediate descendent) of
        other.
        """
        return self.descendentOf(other) and self.depth == other.depth+1


    def ancestorOf(self, other):
        """
        Test if this instance is an ancestor of other.
        """
        return self.path == other.path[:self.depth] and \
                self.depth < other.depth


    def parentOf(self, other):
        """
        Test if this instance is the parent (i.e. the immediate ancestor) of
        other.
        """
        return self.ancestorOf(other) and self.depth == other.depth-1


    @property
    def parent(self):
        """
        Return an ltree representing the parent.
        """
        return ltree('.'.join(self.path[:-1]))


    def __eq__(self, other):
        return self.path == other.path


    def __str__(self):
        return '.'.join(self.path)



if __name__ == '__main__':

    import unittest

    class TestPath(unittest.TestCase):

        def test_parsing(self):
            self.assertEquals(ltree('a').path, ['a'])
            self.assertEquals(ltree('a.b').path, ['a', 'b'])

        def test_equality(self):
            self.assertTrue(ltree('a') == ltree('a'))
            self.assertTrue(ltree('a.b') == ltree('a.b'))
            self.assertFalse(ltree('a') == ltree('a.b'))
            self.assertFalse(ltree('a.b') == ltree('a'))
            self.assertFalse(ltree('a') == ltree('b'))

        def test_child(self):
            self.assertEquals(ltree('a').child('b'), ltree('a.b'))
            self.assertEquals(ltree('a').child('b', 'c'), ltree('a.b.c'))

        def test_depth(self):
            self.assertEquals(ltree('a.b').depth, 2)

        def test_descendentOf(self):
            self.assertTrue(ltree('a.b').descendentOf(ltree('a')))
            self.assertTrue(ltree('a.b.c').descendentOf(ltree('a')))
            self.assertTrue(ltree('a.b.c.d.e.f').descendentOf(ltree('a.b.c')))
            self.assertFalse(ltree('a.b').descendentOf(ltree('b')))
            self.assertFalse(ltree('a.b').descendentOf(ltree('a.b')))
            self.assertFalse(ltree('a').descendentOf(ltree('a.b')))

        def test_ancestorOf(self):
            self.assertTrue(ltree('a').ancestorOf(ltree('a.b')))
            self.assertTrue(ltree('a').ancestorOf(ltree('a.b.c')))
            self.assertFalse(ltree('b').ancestorOf(ltree('a.b')))
            self.assertFalse(ltree('a').ancestorOf(ltree('a')))
            self.assertFalse(ltree('a.b').ancestorOf(ltree('a')))

        def test_parent(self):
            self.assertEquals(ltree('a.b').parent, ltree('a'))
            self.assertEquals(ltree('a.b.c.d').parent, ltree('a.b.c'))
            self.assertNotEqual(ltree('a').parent, ltree('a'))

        def test_str(self):
            for value in ['a', 'a.b', 'b.p.d.r']:
                self.assertEquals(str(ltree(value)), value)

        def test_childOf(self):
            self.assertTrue(ltree('a.b').childOf(ltree('a')))
            self.assertTrue(ltree('a.b.c').childOf(ltree('a.b')))
            self.assertFalse(ltree('a.b').childOf(ltree('a.b')))
            self.assertFalse(ltree('a.b.c').childOf(ltree('a')))
            self.assertFalse(ltree('a.b').childOf(ltree('c')))

        def test_parentOf(self):
            self.assertTrue(ltree('a').parentOf(ltree('a.b')))
            self.assertTrue(ltree('a.b').parentOf(ltree('a.b.c')))
            self.assertFalse(ltree('a.b').parentOf(ltree('a.b.c.d')))
            self.assertFalse(ltree('a.b').parentOf(ltree('a')))
            self.assertFalse(ltree('a.b').parentOf(ltree('c')))

    unittest.main()

