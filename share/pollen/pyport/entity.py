from pollen.pyport import collection, column, error, metadata, relation

class Identity(object):
    '''The identity of an object, can be one or more of the entity's columns'''
    def __init__(self, attributes, factory=None):
        if not isinstance(attributes, (tuple, list)):
            attributes = (attributes,)
        self.attributes = attributes
        self.factory = factory

def getter_factory(property_name):
    def func(self):
        return self._pyport_get_property(property_name)
    return func

def setter_factory(property_name):
    def func(self, value):
        self._pyport_set_property(property_name, value)
    return func

class metaEntity(type):
    '''
    Entity meta class.

    I am responsible for the following:
      * Gathering all Column class attributes into list.
      * Turning each Column class attributes into Python property.
    '''

    def __new__(cls, classname, bases, classdict):

        md = metadata.parse_classdict(classname, classdict)

        # Fall through if there are columns
        if not md.columns:
            return type.__new__(cls, classname, bases, classdict)

        # Create get properties for identity columns
        for name in md.identity.attributes:
            classdict[name] = property(getter_factory(name))

        # Create get and set properties for non-identity columns
        for name, value in md.columns.items():
            if name not in md.identity.attributes:
                classdict[name] = property(
                        getter_factory(name),
                        setter_factory(name),
                        )

        # Create lazy delta list for each to many relation
        for name, value in md.relations.items():
            if isinstance(value,relation.ToManyRelation):
                classdict[name]= collection.LazyDeltaList(name, value)

        # Create property for each to one relation
        for name, value in md.relations.items():
            if isinstance(value,relation.ToOneRelation):
                classdict[name] = property(getter_factory(name),setter_factory(name))

        # Clean up the classdict a bit
        del classdict['_pyport_identity']
        del classdict['_pyport_table']

        # Store the metadata
        classdict['_pyport_metadata'] = md

        # Whoopee! Time to *really* create the class.
        entity_class = type.__new__(cls, classname, bases, classdict)

        # Register the class's metadata
        metadata.register(entity_class)

        return entity_class


class Entity(object):
    '''
    Entity base class.
    '''

    __metaclass__ = metaEntity

    def __init__(self, **kw):

        # Create support data structures
        self._pyport_new = True
        self._pyport_data = {}
        self._pyport_dirty = False
        self._pyport_dirty_list = {}
        self._pyport_session = None

        # Create data item entries
        for name in self._pyport_metadata.columns.keys():
            self._pyport_data[name] = None

        for name in self._pyport_metadata.relations.keys():
            self._pyport_data[name] = None

        # Initialise values in the keyword args
        for name, value in kw.items():
            if name not in self._pyport_metadata.columns.keys():
                raise error.NoSuchAttributeError('Unknown attribute %s'%name)
            setattr(self, name, value)
            del kw[name]

    #
    # Dirty methods
    #

    def set_dirty(self, dirty=True):
        self._pyport_dirty = dirty
        if not dirty:
            self._pyport_dirty_list = {}
        if dirty:
            self.register_as_dirty()

    def is_dirty(self):
        return self._pyport_dirty or (self._pyport_dirty_list and 1 or 0)

    def register_as_dirty(self):
        if self._pyport_session and self._pyport_session():
            self._pyport_session().add_update(self)

    #
    # Property access
    #

    def _pyport_get_property(self, name):
        '''Get the property's value from the data dictionary'''
        return self._pyport_data[name]

    def _pyport_set_property(self, name, value):
        '''
        Record the property's value in the data dictionary and, if it has
        changed, mark the property as dirty.
        '''
        if self._pyport_data[name] != value:
            self._pyport_data[name] = value
            self._pyport_dirty_list[name] = 1
            self.register_as_dirty()

    ##
    # Pickling/serialisation
    #

    def __getstate__(self):
        return (
            self._pyport_data, 
            self._pyport_dirty_list, 
            self._pyport_dirty,
            self._pyport_new)

    def __setstate__(self, state):
        self._pyport_data = state[0]
        self._pyport_dirty_list = state[1]
        self._pyport_dirty = state[2]
        self._pyport_new = state[3]
        self._pyport_session = None

    ##
    # String representation 
    #

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        class_name = '%s.%s'%(self.__class__.__module__,self.__class__.__name__)
        args = ['%s=%s'%(key,val) for key, val in self._pyport_data.items()]
        return '%s(%s)'%(class_name,','.join(args))

