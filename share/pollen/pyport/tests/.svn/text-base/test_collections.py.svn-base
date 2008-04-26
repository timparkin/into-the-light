import unittest
from pollen.pyport import collection

class Test:
    pass
    
def get_counts(l):
    '''Return current, added and removed lengths as a tuple'''
    return (len(l.current),len(l.added),len(l.removed))

class BasicTest(unittest.TestCase):

    def test_00_creation(self):
        l = collection.DeltaList()

    def test_01_append(self):
        l = collection.DeltaList()
        l.append(Test())
        self.failIf(get_counts(l) != (1,1,0))
        l.append(Test())
        self.failIf(get_counts(l) != (2,2,0))
        
    def test_02_extend(self):
        l = collection.DeltaList()
        l.extend((Test(), Test()))
        self.failIf(get_counts(l) != (2,2,0))
        
    def test_03_remove(self):
        l = collection.DeltaList()
        ts = (Test(), Test())
        l.append(ts[0])
        l.append(ts[1])
        l.remove(ts[0])
        self.failIf(get_counts(l) != (1,1,0))
        l.remove(ts[1])
        self.failIf(get_counts(l) != (0,0,0))
        
    def test_04_del(self):
        l = collection.DeltaList()
        t = Test()
        l.append(t)
        del l[0]
        self.failIf(get_counts(l) != (0,0,0))

    def test_05_delslice(self):
        l = collection.DeltaList()
        l.append(Test())
        l.append(Test())
        del l[0:2]
        self.failIf(get_counts(l) != (0,0,0))

    def test_06_slice_update(self):
        l = collection.DeltaList()
        l.append(Test())
        l.append(Test())
        l.snapshot()
        l[0] = Test()
        self.failIf(get_counts(l) != (2,1,1))
        l[0:2] = [Test(), Test()]
        self.failIf(get_counts(l) != (2,2,2))
        l[:] = [Test(), Test()]
        self.failIf(get_counts(l) != (2,2,2))
        l[:] = [Test(), Test(), Test()]
        self.failIf(get_counts(l) != (3,3,2))
        
    def test_07_test_bad_slice_update(self):
        l = collection.DeltaList()
        for i in xrange(3):
            l.append(i)
        l.snapshot()

    def test_08_assign_same(self):
        l = collection.DeltaList()
        for i in xrange(3):
            l.append(i)
        l.snapshot()
        l[:] = l[:]
        self.failIf(get_counts(l) != (3,0,0))
        l[0:2] = l[0:2]
        self.failIf(get_counts(l) != (3,0,0))
        l[1:3] = l[0:2]
        self.failIf(get_counts(l) != (3,1,1))
        
unittest.main()
