from pollen.pyport import error

class DeltaList(object):
    '''A list like object that also keeps track of additions and removals'''
    
    def __init__(self, sequence=None):
        self.added = []
        self.removed = []
        if sequence:
            self.current = [e for e in sequence]
        else:
            self.current = []
        
    def snapshot(self):
        self.added = []
        self.removed = []

    def has_changes(self):
        return len(self.added)>0 | len(self.removed)>0

    def changed(self):
        '''Called when any changes have been made.'''

    #
    # Typical list methods
    #
        
    def append(self, o):
        self._append(o)
        self.changed()
        
    def _append(self, o):
        if o in self.removed:
            self.removed.remove(o)
        else:
            self.added.append(o)
        self.current.append(o)
        
    def extend(self, os):
        for o in os:
            self._append(o)
        self.changed()
        
    def insert(self, idx, o):
        if o in self.removed:
            self.removed.remove(o)
        else:
            self.added.append(o)
        self.current.insert(idx,o)
        self.changed()
        
    def remove(self, o):
        self.remove_delta(o)
        self.current.remove(o)
        self.changed()

    def pop(self, idx):
        o = self.current[idx]
        self.remove(o)
        return o

    def remove_delta(self, o):
        '''Updated added and deleted for a removed object'''
        if o in self.added:
            self.added.remove(o)
        else:
            self.removed.append(o)

    #
    # Emulate a container type
    #
        
    def __len__(self):
        return len(self.current)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.current[key]
        else:
            if not key.start and not key.stop and not key.step:
                return self.current[:]
            elif key.start and not key.stop and not key.step:
                return self.current[key.start:]
            elif not key.start and key.stop and not key.step:
                return self.current[:key.stop]
            elif not key.start and not key.stop and key.step:
                return self.current[::key.step]
            elif key.start and key.stop and not key.step:
                return self.current[key.start:key.stop]
            elif not key.start and key.stop and key.step:
                return self.current[:key.stop:key.step]
            elif key.start and not key.stop and key.step:
                return self.current[key.start::key.step]
            elif key.start and key.stop and not key.step:
                return self.current[key.start:key.stop]

    def __setitem__(self, key, values):
        
        # Return immediately if same object
        if values is self:
            return
            
        # Make key a slice if it isn't already
        if isinstance(key, int):
            key = slice(key, key+1)
        # Make values a sequence if it isn't already
        try:
            for v in values: pass
        except TypeError:
            values = (values,)
            
        # Work out what is being replaced
        slice_objs = self.__getitem__(key)
        
        # Make the change to the real list
        if key.stop:
            self.current[key.start or 0:key.stop] = values
        else:
            self.current[key.start or 0:] = values
            
        # Record the delta changes. This takes into account objects that are
        # being removed _and_ added and doesn't delta them.
        if not values:
            for obj in slice_objs:
                self.remove_delta(obj)
        else:
            for obj in [o for o in slice_objs if o not in values]:
                self.remove_delta(obj)
            self.added.extend([o for o in values if o not in slice_objs])
            
        self.changed()

    def __delitem__(self, key):
        objs = self.__getitem__(key)
        try:
            for obj in objs:
                self.remove(obj)
        except TypeError:
            self.remove(objs)

    def __iter__(self):
        for item in self.current:
            yield item
            
    #
    # Standard string representation stuff
    #
        
    def __str__(self):
        return self.current.__str__()
        
    def __repr__(self):
        return self.current.__repr__()
        

class OwnedDeltaList(DeltaList):
    def __init__(self, owner, sequence=None):
        self.owner = owner
        super(OwnedDeltaList, self).__init__(sequence)
    def changed(self):
        self.owner.set_dirty()


class LazyDeltaList(object):
    '''Lazy loading delta list which tries to load on first access'''

    def __init__(self, name, metadata):
        '''
        name: name of the relation attribute
        metadata: metadata describing the relationship
        '''
        self.name = name
        self.metadata = metadata

    def __get__(self, obj, objtype):
        '''Load the relation if it doesn't exist yet'''
        val = obj._pyport_data.get(self.name)
        if val is None:
            if obj._pyport_new:
                val = obj._pyport_data[self.name] = OwnedDeltaList(obj)
            else:
                val = self.load(obj)
        return val

    def __set__(self, obj, newval):
        val = obj._pyport_data.get(self.name)
        if val is None:
            val = obj._pyport_data[self.name] = OwnedDeltaList(obj)
        val[:] = newval

    def load(self, obj):
        '''*Really* load the data'''
        sess = obj._pyport_session
        if sess is None or not sess():
            msg = 'cannot retrieve %s relation'%self.name
            raise error.SessionExpired, msg
        else:
            sess = sess()
        entity_type = self.metadata.entity_class_name
        where_clause = ['%s=%%s'%a for a in self.metadata.join_attrs]
        where_clause = ' and '.join(where_clause)
        parameters = [getattr(obj, name) for name in obj._pyport_metadata.identity.attributes]
        query = 'from %s as o where %s'%(entity_type, where_clause)
        if self.metadata.order:
            query = '%s order by %s' % (query, self.metadata.order)
        rs = sess.find(query, parameters)
        l = obj._pyport_data[self.name] = OwnedDeltaList(obj, rs)
        return l
