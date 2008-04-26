"""
TODO:

    * Should permissions be hierarchical? It doesn't make much sense to have
      the "a.b" permission without automatically having the 'a' permission.

    * Provide an exception-causing check method that can be used at the top of
      methods and will immediately raise an error, stopping any further
      processing.
"""



from itertools import chain



class ACLError(Exception):
    """
    General ACL error.
    """



class ACLParseError(ACLError):
    """
    ACL configuration parsing error.
    """



class ACLAmbiguous(ACLError):
    """
    Ambiguous ACL permission error.
    """



class ACL(object):


    def __init__(self, root):
        self.root = root
 
 
    def hasAccess(self, roles, permission):

        if not roles:
            roles = ['Root']
 
        # Build a set of all applicable roles
        roles = applicableRoles(roles)
 
        # No access by default
        access = False
 
        # No recursion here
        rolesIter = iter([self.root])
 
        while True:
 
            # Get the next node
            try:
                role = rolesIter.next()
            except StopIteration:
                break
 
            # Test for a match on the role
            if role.name in roles:
                if 'ALL' in role.deny or permission in role.deny:
                    access = False
                elif 'ALL' in role.allow or permission in role.allow:
                    access = True
 
            # Recurse into children
            if role.childRoles:
                rolesIter = chain(iter(role.childRoles), rolesIter)
 
        return access



def applicableRoles(roles_):
    roles = set()
    for role in roles_:
        role = role.split('.')
        for i in range(1, len(role)+1):
            roles.add('.'.join(role[:i]))
    return roles



class Role(object):


    EMPTY_SET = frozenset()
 
 
    def __init__(self, name, allow, deny):
        self.name = name
        self.allow = allow or Role.EMPTY_SET
        self.deny = deny or Role.EMPTY_SET
        self.childRoles = []



def createPermissiveACL():
    """
    Create a permissive ACL, i.e. one that always says access is ok.
    """
    return createACLFromSimpleConfig(["Root +ALL"])


    
def createACLFromSimpleConfig(config):
    """
    Create an ACL from the given config. Config can be anything iterable where
    each yielded item is a line of text, i.e. an open file, a sequence of
    lines, etc.
    """

    def sanitize(lines):
        """
        Strip lines and remove empty lines and comments.
        """
        lines = (line.strip() for line in lines)
        lines = (line for line in lines if line and line[0] != '#')
        return lines
 
    def parsePermissions(permissions):
        """
        Parse the permissions into two sets of allows and denies.
        """
        allow = set()
        deny = set()
        for permission in permissions.split():
            if permission[0] == '+':
                allow.add(permission[1:])
            elif permission[0] == '-':
                deny.add(permission[1:])
            else:
                raise ACLParseError("Invalid permissions specification, %r" %
                        permissions)
        return allow, deny
 
    def parentRole(role):
        role = role.rsplit('.', 1)
        if len(role) == 1:
            return None
        else:
            return role[0]
 
    roleLookup = {}
 
    # Iterate the lines in the config
    for line in sanitize(config):
 
        # Extract the role and permissions from the line
        line = line.split(None, 1)
        role = line[0]
        if len(line) == 1:
            allow, deny = None, None
        else:
            allow, deny = parsePermissions(line[1])
 
        # Split the role name into parent and child
        parent = parentRole(role)
 
        # Create the node
        node = Role(role, allow, deny)
 
        # Add the node to its parent
        if parent is not None:
            roleLookup[parent].childRoles.append(node)
 
        # Record this node for quick lookup
        roleLookup[role] = node
 
    return ACL(roleLookup['Root'])
