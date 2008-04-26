import gc, types
from twisted.python import reflect

def gcstats(io, objTypes, maxdepth=0):
    objTypes = map(reflect.namedAny, objTypes)
    gc.collect()
    objects = gc.get_objects()
    try:
        for objType in objTypes:
            logtype(io, objects, objType, maxdepth)
    except Exception, e:
        print e
    io.flush()
    
def logtype(io, objects, objType, maxdepth):
    objects = [obj for obj in objects if isinstance(obj, objType)]
    referrers = gc.get_referrers(*objects)
    print >> io, '---- %s' % objType.__name__
    print >> io, 'total: %d' % len(objects)
    print >> io, 'total referrers: %d' % len(referrers)
    if maxdepth:
        for obj in objects:
            logreferraltree(io, obj, referrers, maxdepth)
        
def logreferraltree(io, obj, referrers, maxdepth, depth=0):
    objClass = obj.__class__
    if objClass.__module__ == '__builtin__':
        objClassName = objClass.__name__
    else:
        objClassName = '%s.%s' % (objClass.__module__, objClass.__name__)
    print >> io, '%s%s %s @ %s' % ('  '*depth, depth and '+' or '-', objClassName, hex(id(obj)))
    if depth < maxdepth-1:
        for referrer in referrers:
            if type(referrer) is types.FrameType:
                continue
            logreferraltree(io, referrer, gc.get_referrers(referrer), maxdepth, depth+1)
