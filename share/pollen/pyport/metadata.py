from pollen.pyport import column, error, relation

'''
Registry for all types known to pyport.
'''

# All known types
types_dict = {}

class MetaData:

    def __init__(self):
        self.columns = {}
        self.relations = {}
        self.identity = None
        self.table = None

    def identity_attribute_names(self):
        return self.identity.attributes

    def identity_column_names(self):
        return [self.columns[attr].name for attr in self.identity.attributes]

    def non_identity_attribute_names(self):
        all_attrs = self.all_attribute_names()
        id_attrs = self.identity_attribute_names()
        return [attr for attr in all_attrs if attr not in id_attrs]

    def non_identity_column_names(self):
        all_cols = self.all_column_names()
        id_cols = self.identity_column_names()
        return [col for col in all_cols if col not in id_cols]

    def all_attribute_names(self):
        return self.columns.keys()

    def all_column_names(self):
        return [col.name for col in self.columns.values()]

def parse_classdict(classname, classdict):

    md = MetaData()

    # Find columns
    for name, value in classdict.items():
        if isinstance(value, column.Column):
            md.columns[name] = value

    # Set column name to the same as the class attribute if its missing
    for name, col in md.columns.items():
        if not col.name:
            col.name = name

    # Find relations
    for name, value in classdict.items():
        if isinstance(value, relation.Relation):
            md.relations[name] = value

    # Nothing more to do if there are no columns
    if not md.columns:
        return md

    # Find the identity
    md.identity = classdict.get('_pyport_identity')
    if not md.identity:
        raise error.ConfigurationError(
            'No identity for %s, please set the _pyport_identity class attribute' % classname)

    # Find the table name
    table = classdict.get('_pyport_table')
    if not table:
        raise error.ConfigurationError(
            'No table for %s, please set the _pyport_table class attribute' % classname)

    md.table = table

    return md

def register(entity_class):
    '''Register an entity class with the system'''
    full_class_name = '%s.%s'%(entity_class.__module__, entity_class.__name__)
    types_dict[full_class_name] = entity_class

def type_by_name(entity_class_name):
    return types_dict[entity_class_name]
