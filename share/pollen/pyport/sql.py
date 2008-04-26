from __future__ import generators

'''
SQL generation functions.
'''

def insert_sql(entity_type):
    '''Build the SQL to insert the entity'''
    table = entity_type._pyport_metadata.table
    cols = entity_type._pyport_metadata.all_column_names()
    args = ','.join(['%%(%s)s'%col for col in cols])
    return 'insert into %s (%s) values (%s)' % (table, ','.join(cols), args)
    
def update_sql(entity_type, cols=None):
    '''Build the SQL to update an entity'''
    if not cols:
        cols = entity_type._pyport_metadata.non_identity_column_names()
    id_cols = entity_type._pyport_metadata.identity_column_names()
    table = entity_type._pyport_metadata.table
    set_clause = ','.join(['%s=%%(%s)s'%(col,col) for col in cols])
    where_clause = ' and '.join(['%s=%%(%s)s'%(col,col) for col in id_cols])
    return 'update %s set %s where %s' % (table, set_clause, where_clause)
    
def delete_sql(entity_type):
    '''Build the SQL to delete an entity'''
    id_cols = entity_type._pyport_metadata.identity_column_names()
    table = entity_type._pyport_metadata.table
    where_clause = ' and '.join(['%s=%%(%s)s'%(col,col) for col in id_cols])
    return 'delete from %s where %s' % (table, where_clause)
    
def select_sql(entity_type):
    '''
    Build the SQL for a select clause
    
    entity_type: Entity class
    '''
    table = entity_type._pyport_metadata.table
    cols = entity_type._pyport_metadata.all_column_names()
    return 'select %s from %s' % (','.join(cols), table)

def select_by_identity_sql(entity_type):
    '''
    Build the SQL for a select by identity clause
    
    entity_type: Entity class
    '''
    cols = entity_type._pyport_metadata.all_column_names()
    where_cols = entity_type._pyport_metadata.identity_column_names()
    select_clause = ','.join(cols)
    where_clause = ' and '.join(['%s=%%s' % col for col in where_cols])
    parts = (select_clause, entity_type._pyport_metadata.table, where_clause)
    return 'select %s from %s where %s' % parts

