"""
Generators for iterating over various permutations of lists.
"""

def xcombinations(items, n):
    if n==0: yield []
    else:
        for i in xrange(len(items)):
            for cc in xcombinations(items[:i]+items[i+1:],n-1):
                yield [items[i]]+cc

def xuniqueCombinations(items, n):
    if n==0: yield []
    else:
        for i in xrange(len(items)):
            for cc in xuniqueCombinations(items[i+1:],n-1):
                yield [items[i]]+cc
            
def xselections(items, n):
    if n==0: yield []
    else:
        for i in xrange(len(items)):
            for ss in xselections(items, n-1):
                yield [items[i]]+ss

def xpermutations(items):
    return xcombinations(items, len(items))

def nloop(lists):

    size = len(lists)
    slots = [None]*size

    def generator(lists,pos):
        if len(lists) == 0: # Nothing more, yield a result and return
            yield slots[:]
            return
        for i in lists[0]:
            slots[pos] = i # Fill in the slot
            for x in generator(lists[1:],pos+1): # Recurse
                yield x

    return generator(lists,0)
