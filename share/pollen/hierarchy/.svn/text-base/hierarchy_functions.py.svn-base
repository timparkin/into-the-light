# Get all root id's

def cmbd_get_all_root_nodes(self):
    # Get the top level node
    curs = self.conn.cursor()
    # Get all nodes between the top levels left and right nodes
    curs.execute('''
                 SELECT
                     id,
                     object,
                     group_id,
                     lft_node,
                     rgt_node,
                     parent
                 FROM
                     hierarchy
                 WHERE
                     parent = 0
                 ORDER BY
                     group_id
                 ''')
    nodes = curs.fetchall()
    root_nodes = []
    for node in nodes:
        root_nodes.append(dict(zip(('id', 'object', 'group_id', 'lft_node', 'rgt_node', 'parent'), node)))
    curs.close()
    return root_nodes

def nstd_get_all_root_nodes(self, id):
    pass

def adjc_get_all_root_nodes(self, id):
    pass

def adjc_get_all_root_nodes(self, id):
    # Get the top level node
    curs = self.conn.cursor()
    # Get all nodes between the top levels left and right nodes
    curs.execute('''
                 SELECT
                     id,
                     object,
                     group_id,
                     lft_node,
                     rgt_node,
                     parent
                 FROM
                     hierarchy
                 WHERE
                     parent = 0
                 ORDER BY
                     group_id
                 ''')
    nodes = curs.fetchall()
    root_nodes = []
    for node in nodes:
        root_nodes.append(dict(zip(('id', 'object', 'group_id', 'lft_node', 'rgt_node', 'parent'), node)))
    curs.close()
    return root_nodes
    
# Add New Tree

def cmbd_add_new_tree(self, group_id, object):
    # Get the top level node
    curs = self.conn.cursor()
    # Get all nodes between the top levels left and right nodes
    curs.execute('''
                 INSERT INTO
                     hierarchy
                 VALUES (NULL, %(object)s, %(group_id)s, 1, 2, 0)
                 ''', { 'group_id':group_id, 'object':object })
    curs.execute('''
                 SELECT
                     id 
                 FROM
                     hierarchy
                 WHERE
                     object = %(object)s AND
                     group_id = %(group_id)s AND
                     lft_node = 1 AND
                     rgt_node = 2 AND
                     parent = 0
                 ''', { 'group_id':group_id, 'object':object })
    node_id = curs.fetchone()[0]
    curs.close()
    return node_id

def nstd_add_new_tree(self, id):
    pass

def adjc_add_new_tree(self, id):
    pass

# Get Subtree

def cmbd_get_subtree_for_group(self, group_id):
    """Retrieve a subtree by first looking up the root node for the group"""
    curs = self.conn.cursor()
    try:
        curs.execute('select id from hierarchy where group_id=%s and parent=0', (group_id,))
        return self.get_subtree(curs.fetchone()[0])
    finally:
        curs.close()
    
def cmbd_get_subtree(self, id):
    """ Combined Method to get Subtree"""
    # Get the top level node
    top_node = self.get_node(id)
    curs = self.conn.cursor()
    # Get all nodes between the top levels left and right nodes
    curs.execute('''
                 SELECT
                     id,
                     object,
                     group_id,
                     lft_node,
                     rgt_node,
                     parent
                 FROM
                     hierarchy
                 WHERE
                     lft_node >= %(top_lft_node)s and
                     rgt_node <= %(top_rgt_node)s and
                     group_id = %(group_id)s
                 ORDER BY
                     lft_node
                 ''', {'top_lft_node':top_node['lft_node'], 'top_rgt_node':top_node['rgt_node'], 'group_id':top_node['group_id']})
    subtree_nodes = curs.fetchall()
    curs.close()
    return subtree_nodes

def nstd_get_subtree(self, id):
    pass

def adjc_get_subtree(self, id):
    pass

# Internal Get Node function    

def cmbd_get_node(self, id):
    curs = self.conn.cursor()
    # Get a nodes attributes
    curs.execute('''
                 SELECT
                     id,
                     object,
                     group_id,
                     lft_node,
                     rgt_node,
                     parent
                 FROM
                     hierarchy
                 WHERE
                     id = %(id)s
                 ''', {'id':id})
    # Compile into a dictionary
    node = dict(zip(('id', 'object', 'group_id', 'lft_node', 'rgt_node', 'parent'), curs.fetchone()))
    curs.close()
    return node

def nstd_get_node(self, id):
    pass

def adjc_get_node(self, id):
    pass

# Internal Insert Node Function  

def cmbd_insert_node(self, parent_node, object, group_id, before=None, after=None):

    if before is not None and after is not None:
        raise ValueError('Only use one of before and after')

    curs = self.conn.cursor()

    target_node = None
    position = False

    if before:
        target_node = before
        position = True
    if after:
        target_node = after

    curs.execute('''SELECT insert_node( %(parent_node)s, %(target_node)s, %(position)s, %(object)s, %(group_id)s )''', { 'parent_node':parent_node, 'target_node':target_node, 'position': position, 'object':object, 'group_id':str(group_id) })

    node_id = curs.fetchone()[0]
    curs.close()
    return node_id

def nstd_insert_node(self, id):
    pass

def adjc_insert_node(self, id):
    pass

# Internal Delete Node Function  

def cmbd_delete_node(self, node_id):
    curs = self.conn.cursor()
    # Get a nodes attributes
    curs.execute('''
                 SELECT delete_node ( %(node_id)s )
                 ''', {'node_id':node_id})
    curs.close()

def nstd_delete_node(self, id):
    pass

def adjc_delete_node(self, id):
    pass

# Internal Swap Nodes Function  

def cmbd_swap_nodes(self, id_a, id_b):
    curs = self.conn.cursor()
    # Get a nodes attributes
    curs.execute('''
                 SELECT swap_nodes (%(id_a)s, %(id_b)s)
                 ''', {'id_a':id_a, 'id_b':id_b})
    curs.close()

def nstd_swap_nodes(self, id):
    pass

def adjc_swap_nodes(self, id):
    pass

# Internal Move To Function 

def cmbd_move_to(self, node_a_id, parent_node, target_node=None, position=True):
    curs = self.conn.cursor()
    # Insert the node
    if target_node is None or target_node == 'Null':
        curs.execute('''SELECT move_to( %(node_a_id)s, %(parent_node)s, NULL, True )''', { 'node_a_id':node_a_id, 'parent_node':parent_node })
    else:
        if position == True or position == 'True':
            curs.execute('''SELECT move_to( %(node_a_id)s, 0, %(target_node)s, True )''', { 'node_a_id':node_a_id, 'target_node':target_node })
        else:
            curs.execute('''SELECT move_to( %(node_a_id)s, 0, %(target_node)s, False )''', { 'node_a_id':node_a_id, 'target_node':target_node })
    curs.close()

def nstd_move_to(self, id):
    pass

def adjc_move_to(self, id):
    pass

# Internal Move Direction Function 

def cmbd_move(self, node_id, direction):
    curs = self.conn.cursor()
    # Insert the node
    if direction == 'up':
        curs.execute('''
                 SELECT move_up( %(node_id)s ) 
                 ''', {'node_id':node_id })
    else:
        curs.execute('''
                 SELECT move_down( %(node_id)s ) 
                 ''', {'node_id':node_id })
    curs.close()

def nstd_move(self, id):
    pass

def adjc_move(self, id):
    pass


# Internal Update Node 

def cmbd_update_node(self, id, object):
    curs = self.conn.cursor()
    # Insert the node
    curs.execute('''
                 UPDATE
                     hierarchy
                 SET
                     object = %(object)s
                 WHERE
                     id = %(id)s
                 ''', {'id':id, 'object':object})
    curs.close()

def nstd_update_node(self, id):
    pass

def adjc_update_node(self, id):
    pass

# Update Group Id

def cmbd_update_group_id(self, old_group_id, group_id):
    curs = self.conn.cursor()
    # Insert the node
    curs.execute('''
                 UPDATE
                     hierarchy
                 SET
                     group_id = %(group_id)s
                 WHERE
                     group_id = %(old_group_id)s
                 ''', {'group_id':group_id, 'old_group_id':old_group_id})
    curs.close()

def nstd_update_group_id(self, id):
    pass

def adjc_update_group_id(self, id):
    pass
