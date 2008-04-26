# -*- coding: utf-8 -*-

"""
YAML Configuration module.

The module is really just an extension of pysyck that supports the inclusion of
YAML files at any part of the main YAML document by specifiying a !cfg/include
type in front of the name of the file to include::

    - foo
    - bar
    - !!cfg/include: another.yml

Note: this module uses yamlutil so all scalars are treated as UTF-8 encoded
strings.
"""


import os
from pollen import yamlutil



class Loader(yamlutil.Loader):


    def __init__(self, parent, *a, **kw):
        yamlutil.Loader.__init__(self, *a, **kw)
        self.parent = parent


    def construct_private_cfg_include(self, node):
        """
        Include an external file in the document.
        """
        c = YAMLConfig(node.value)
        self.parent._includes.append(c)
        return c



class YAMLConfig(object):



    def __init__(self, filename, loaderFactory=None):
        self.filename = filename
        self._data = None
        self._mtime = None
        self._includes = []
        if loaderFactory is not None:
            self.loaderFactory = loaderFactory


    def loaderFactory(self,*a, **kw):
        return Loader(self, *a, **kw)


    def __len__(self):
        return len(self.data)


    def __getitem__(self, key):
        return self.data[key]


    def __iter__(self):
        return iter(self.data)


    def __repr__(self):
        return repr(self.data)


    def __contains__(self, item):
        return item in self.data


    def get(self, name, default=None):
        return self.data.get(name, default)


    def find(self, path):

        if path[0] != '/':
            raise ValueError("Only absolute paths are supported.")

        # Parse the path into a sequence of keys
        keys = path.split('/')[1:]
        if keys == ['']:
            keys = []

        node = self.data

        try:
            for key in keys:
                node = node[key]
        except:
            return None

        return node


    def _getData(self):
        mtime = os.path.getmtime(self.filename)
        if self._mtime is None or self._mtime < mtime:
            self._mtime = mtime
            f = file(self.filename)
            try:
                self._data = yamlutil.load(f, Loader=self.loaderFactory)
            finally:
                f.close()
        return self._data

    data = property(_getData)


    def hasChanges(self):
        """
            This returns True if the yaml file has been read (self._mtime is not None)
            and the mtime of the file has changed, or if any of the yaml files that are
            included have changes.
        
            If the yaml file has not been read, then self._mtime is None.
        """
        if self._mtime is None:
            return False

        mtime = os.path.getmtime(self.filename)
        if self._mtime < mtime:
            return True

        for inc in self._includes:
            if inc.hasChanges():
                return True

        return False



def load(filename):
    return YAMLConfig(filename)



if __name__ == '__main__':

    import os
    import tempfile
    import unittest
    import time

    POUND = "£".decode("utf-8")

    class BaseTestCase(unittest.TestCase):

        def __init__(self, *a, **k):
            unittest.TestCase.__init__(self, *a, **k)
            self.__tempFiles = []

        def makeTempFile(self, content=None):
            f, filename = tempfile.mkstemp()
            if content is not None:
                os.write(f, content)
            os.close(f)
            self.__tempFiles.append(filename)
            return filename

        def tearDown(self):
            for filename in self.__tempFiles:
                os.remove(filename)

    class TestCase(BaseTestCase):

        def test_load(self):
            cfg = load(self.makeTempFile('''- foo'''))
            self.assertEquals(cfg[0], "foo")

        def test_len(self):
            cfg = load(self.makeTempFile('''- foo\n- bar'''))
            self.assertEquals(len(cfg), 2)

        def test_indexAccess(self):
            cfg = load(self.makeTempFile('''- foo'''))
            self.assertEquals(cfg[0], "foo")

        def test_keyItemAccess(self):
            cfg = load(self.makeTempFile('''foo: bar'''))
            self.assertEquals(cfg["foo"], "bar")
            self.assertRaises(KeyError, lambda: cfg["missing"])

        def test_iter(self):
            cfg = load(self.makeTempFile('''- foo\n- bar'''))
            self.assertEquals(list(cfg), ["foo", "bar"])

        def test_contains(self):
            cfg = load(self.makeTempFile('''foo: bar'''))
            self.assertTrue("foo" in cfg)
            self.assertFalse("missing" in cfg)

        def test_keyGetAccess(self):
            cfg = load(self.makeTempFile('''foo: bar'''))
            self.assertEquals(cfg.get("foo"), "bar")
            self.assertEquals(cfg.get("missing"), None)

        def test_find(self):
            cfg = load(self.makeTempFile('''foo: {bar: fum}'''))
            self.assertEquals(cfg.find("/foo"), {"bar": "fum"})
            self.assertEquals(cfg.find("/foo/bar"), "fum")
            self.assertEquals(cfg.find("/missing"), None)
            self.assertEquals(cfg.find("/missing/still_missing"), None)

        def test_include(self):
            include = self.makeTempFile('''bar: fum''')
            cfg = load(self.makeTempFile('''foo: !!cfg/include: "%s"''' % (include,)))
            self.assertEquals(cfg["foo"]["bar"], "fum")
            self.assertEquals(cfg.find("/foo/bar"), "fum")

        def test_includeReload(self):
            include = self.makeTempFile('''bar: fum''')
            cfg = load(self.makeTempFile('''foo: !!cfg/include: "%s"''' % (include,)))
            self.assertEquals(cfg["foo"]["bar"], "fum")
            self.assertEquals(cfg.find("/foo/bar"), "fum")
            time.sleep(2)
            f = open(include, "w")
            f.write('''bar: foe''')
            f.close()
            self.assertEquals(cfg["foo"]["bar"], "foe")
            self.assertEquals(cfg.find("/foo/bar"), "foe")

        def test_hasChanges(self):
            include = self.makeTempFile('''bar: fum''')
            cfg = load(self.makeTempFile('''fie: anything\nfoo: !!cfg/include: "%s"''' % (include,)))
            self.assertEquals(cfg.hasChanges(), False)
            self.assertEquals(cfg["fie"], "anything")
            self.assertEquals(cfg.hasChanges(), False)
            self.assertEquals(cfg["foo"]["bar"], "fum")
            self.assertEquals(cfg.hasChanges(), False)
            time.sleep(2)
            f = open(include, "w")
            f.write('''bar: foe''')
            f.close()
            self.assertEquals(cfg.hasChanges(), True)

        def test_strings(self):
            cfg = load(self.makeTempFile('''- foo\n- £\n- !python/str £\n- !python.unicode £'''))
            self.assertEquals(list(cfg), [u"foo", POUND, "£", POUND])

        def test_numbers(self):
            cfg = load(self.makeTempFile('''- !int 1\n- !float 2.5'''))
            self.assertEquals(list(cfg), [1, 2.5])
            self.assertEquals(map(type, cfg), [int, float])
            self.assertEquals(map(type, cfg), [int, float])

    unittest.main()

