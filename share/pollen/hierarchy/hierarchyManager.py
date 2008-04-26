from pollen.hierarchy import hierarchy_functions

def create(type, conn):
    # switch on type and return
    if type == 'cmbd':
        return Cmbd(conn)
    elif type == 'nstd':
        return Nstd(conn)
    if type == 'adjc':
        return Adjc(conn)
    if type == 'ltree':
        return LTree(conn)        

    
        
class Hierarchy:    
    def __init__(self, conn):
        self.conn = conn

class Cmbd(Hierarchy):
    get_all_root_nodes = hierarchy_functions.cmbd_get_all_root_nodes
    add_new_tree = hierarchy_functions.cmbd_add_new_tree
    get_subtree = hierarchy_functions.cmbd_get_subtree
    get_subtree_for_group = hierarchy_functions.cmbd_get_subtree_for_group
    get_node = hierarchy_functions.cmbd_get_node
    insert_node = hierarchy_functions.cmbd_insert_node
    delete_node = hierarchy_functions.cmbd_delete_node
    swap_nodes = hierarchy_functions.cmbd_swap_nodes
    move_to = hierarchy_functions.cmbd_move_to
    move = hierarchy_functions.cmbd_move
    update_group_id = hierarchy_functions.cmbd_update_group_id
    
    
class Nstd(Hierarchy):
    get_all_root_nodes = hierarchy_functions.nstd_get_all_root_nodes
    add_new_tree = hierarchy_functions.nstd_add_new_tree
    get_subtree = hierarchy_functions.nstd_get_subtree
    get_node = hierarchy_functions.nstd_get_node
    insert_node = hierarchy_functions.nstd_insert_node
    delete_node = hierarchy_functions.nstd_delete_node
    swap_nodes = hierarchy_functions.nstd_swap_nodes
    move_to = hierarchy_functions.nstd_move_to
    move = hierarchy_functions.nstd_move
    update_group_id = hierarchy_functions.nstd_update_group_id

class Adjc(Hierarchy):
    get_all_root_nodes = hierarchy_functions.adjc_get_all_root_nodes
    add_new_tree = hierarchy_functions.adjc_add_new_tree
    get_subtree = hierarchy_functions.adjc_get_subtree
    get_node = hierarchy_functions.adjc_get_node
    insert_node = hierarchy_functions.adjc_insert_node
    delete_node = hierarchy_functions.adjc_delete_node
    swap_nodes = hierarchy_functions.adjc_swap_nodes
    move_to = hierarchy_functions.adjc_move_to
    move = hierarchy_functions.adjc_move
    update_group_id = hierarchy_functions.adjc_update_group_id
    
#class LTree(Hierarchy):
#    get_all_root_nodes = hierarchy_functions.ltree_get_all_root_nodes
#    add_new_tree = hierarchy_functions.ltree_add_new_tree
#    get_subtree = hierarchy_functions.ltree_get_subtree
#    get_node = hierarchy_functions.ltree_get_node
#    insert_node = hierarchy_functions.ltree_insert_node
#    delete_node = hierarchy_functions.ltree_delete_node
#    swap_nodes = hierarchy_functions.ltree_swap_nodes
#    move_to = hierarchy_functions.ltree_move_to
#    move = hierarchy_functions.ltree_move
#    update_group_id = hierarchy_functions.ltree_update_group_id

    
"""
test.py
-------

import hierarchyManager
hier_mgr = hierarchy_manager.create('combined', conn)
"""
