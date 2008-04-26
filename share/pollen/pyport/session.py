from __future__ import generators

'''
PyPort object editing session.

In essence a Session is a database transaction that provides methods for
acting on a persistent object store.

The main methods for locating objects are load() and find(). Any objects are
cached for the duration of the session to ensure that only one copy of
a particular object exists in memory. Retrieved objects maintain a weaki
connection to the session until the session is garbage collected. The
connection is weak so that objects can exist without the session. Join()
can be used to attach an object to another session.

The main methods for storing objects are save() and join(). Save() registers
a new object with the session and causes a SQL INSERT to executed at some
time. Join() is used to attach an object to the session. It is useful when
an object has been retrieved from a session that no longer exists.

The session can be commited or aborted using commit() and rollback(). Objects
in memory will probably not be consitent with the database after a rollback()
since no attempt is made to rollback the memory version.

Changes to objects in memory are often not immediately reflected in the
database. Calling flush() executes SQL to sync the database. Flush() does not
commit any changes, only commit() will do that.
'''

import re
import weakref
from pollen.pyport import error, metadata, parser, relation, sql

def obj_iter(entity_type, curs, session=None):
    '''
    Iterate over a result set turning each row into an object
    
    entity_type: Entity class
    curs: cursor holding the result set
    '''
    attr_names = entity_type._pyport_metadata.all_attribute_names()
    col_to_attr = zip(xrange(len(attr_names)), attr_names)
    while 1:
        d = {}
        row = curs.fetchone()
        if not row:
            break
        entity = entity_type()
        entity._pyport_new = False
        for col, attr in col_to_attr:
            entity._pyport_data[attr] = row[col]
        if session:
            entity._pyport_session = weakref.ref(session)
        yield entity

class Session:

    parser = parser.Parser()

    def __init__(self, conn):
        '''
        Create a new session.

        A session is the primary interface through which you interact with
        a database.  It is a combination of object store operations and
        transaction control operations.

        conn: manually created database connection
        '''
        self.conn = conn
        self.insertions = []
        self.updates = []
        self.update_ids = {}
        self.deletes = []
        self.delete_ids = {}
        self.caches = {}

    def cache_for(self, entity_type):
        return self.caches.setdefault(entity_type, {})

    def __del__(self):
        self.close()

    def close(self):
        '''Close any resources allocated by the session'''
        pass

    def load(self, entity_type, identity):
        '''Load an object'''
        def _(msg):
            #print msg, id(self), entity_type.__name__, identity
            pass
        cache = self.cache_for(entity_type)
        obj = cache.get(identity, None)
        if obj is not None:
            _(':) cached')
            return obj
        _(':( not cached ')
        curs = self.conn.cursor()
        the_sql = sql.select_by_identity_sql(entity_type)
        curs.execute(the_sql, identity)
        try:
            obj = obj_iter(entity_type, curs, self).next()
        except StopIteration:
            return None
        cache[identity] = obj
        return obj

    def find(self, query, parameters=None):
        '''Find all matching objects'''
        
        # Parse the query
        entity_name, as, where, order_by = Session.parser.parse(query)

        # Get the metadata
        classobj = metadata.type_by_name(entity_name)
        md = classobj._pyport_metadata

        # Build the SELECT ... FROM part
        cols = md.all_column_names()
        table = md.table
        the_sql = 'select %s from %s'%(','.join(cols),table)

        # Add the AS ... WHERE ... part
        if where:
            the_sql = '%s as %s where %s' % (the_sql, as, where)
            
        # Add the order by
        if order_by:
            the_sql = '%s order by %s' % (the_sql, order_by)

        # Run the SQL
        curs = self.conn.cursor()
        if parameters:
            curs.execute(the_sql, parameters)
        else:
            curs.execute(the_sql)

        return obj_iter(classobj, curs, self)

    def save(self, obj):
        '''Save an object to the database'''
        self.insertions.append(obj)

    def join(self, obj):
        '''Include an already saved object in this session'''
        self.join_recursive(obj)

    def join_recursive(self, obj):
        # Mark this for update
        obj._pyport_session = weakref.ref(self)
        if obj.is_dirty():
            self.add_update(obj)
        # Collection objects
        md = obj._pyport_metadata
        for name, rel in md.relations.items():
            if isinstance(rel, relation.ToManyRelation):
                relation_list = getattr(obj, name)
                for obj in relation_list:
                    self.join_recursive(obj)

    def remove(self, obj):
        '''Remove an object from the database'''
        if self.delete_ids.has_key(id(obj)):
            return
        self.deletes.append(obj)
        self.delete_ids[id(obj)] = 1

    def flush(self):
        '''Flush any changes to the database'''
        # Create a cursor to use for the entire flush
        curs = self.conn.cursor()
        # Insertions
        for obj in self.insertions:
            self._insert(curs, obj)
            self._flush_collections(curs, obj)
        self.insertions = []
        # Updates
        for obj in self.updates:
            self._update(curs, obj)
            self._flush_collections(curs, obj)
        self.updates = []
        self.update_ids = {}
        # Collection deletions
        # Collection elements: insertion, updates, deletions
        # Collection insertions
        # Entity deletions
        for obj in self.deletes:
            self._delete(curs, obj)
        self.deletes = []
        self.delete_ids = {}

    def _flush_collections(self, curs, obj):
        md = obj._pyport_metadata
        for name, rel in md.relations.items():
            if isinstance(rel, relation.ToManyRelation):
                relation_list = getattr(obj, name)
                # Deletions
                for item in relation_list.removed:
                    self._delete(curs, item)
                # Insertions
                for item in relation_list.added:
                    id_attrs = md.identity.attributes
                    join_attrs = rel.join_attrs
                    for source, dest in zip(id_attrs, join_attrs):
                        item._pyport_data[dest] = obj._pyport_data[source]
                    self._insert(curs, item)
                    self._flush_collections(curs, item)
                # Updates
                for item in relation_list.current:
                    if item.is_dirty():
                        self._update(curs, item)
                    self._flush_collections(curs, item)
                relation_list.snapshot()

    def commit(self):
        '''Commit any changes to the database'''
        self.flush()
        self.conn.commit()

    def rollback(self):
        '''Rollback (abort) changes''' 
        self.conn.rollback()

    def _insert(self, curs, obj):
        the_sql = sql.insert_sql(obj.__class__)
        obj._pyport_data['id'] = obj._pyport_metadata.identity.factory(curs)[0]
        curs.execute(the_sql, obj._pyport_data)
        obj.set_dirty(False)

    def _update(self, curs, obj):
        the_sql = sql.update_sql(obj.__class__)
        curs.execute(the_sql, obj._pyport_data)
        obj.set_dirty(False)

    def _delete(self, curs, obj):
        the_sql = sql.delete_sql(obj.__class__)
        curs.execute(the_sql, obj._pyport_data)

    def add_update(self, obj):
        if self.update_ids.has_key(id(obj)):
            return
        self.updates.append(obj)
        self.update_ids[id(obj)] = 1
