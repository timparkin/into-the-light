'''
Relation types
'''

class Relation(object):
    def __init__(self, entity_class_name, join_attrs):
        self.entity_class_name = entity_class_name
        if not isinstance(join_attrs, (list, tuple)):
                join_attrs = (join_attrs,)
        self.join_attrs = join_attrs

class ToOneRelation(Relation):
    pass
    
class OneToOne(ToOneRelation):
    pass
    
class ToManyRelation(Relation):
    def __init__(self, entity_class_name, join_attrs, order=None):
        Relation.__init__(self, entity_class_name, join_attrs)
        self.order = order

class OneToMany(ToManyRelation):
    pass
    
class ManyToMany(ToManyRelation):
    pass
