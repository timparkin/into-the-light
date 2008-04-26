'''
Sorting-related utilities.
'''

def dsu(l, attr_name, reverse=False):
    '''
    Generalised decorate-sort-undecorate for for lists or tuples.

    l: list of items to sort
    attr_name: name of the attribute of the items to sort on
    reverse: reverse the sort
    '''

    l = [(getattr(i,attr_name),i) for i in l]
    l.sort()
    if reverse:
        l.reverse()
    return [i[1] for i in l]
