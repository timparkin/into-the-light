import syck 

class rest(str):
    ''' a rest string for converting to html
    '''
    pass

class html(str):
    ''' a html block for converting to html
    '''
    pass

class cmsitemsel(str):
    ''' an item selection object
    '''
    pass

class cmsfragment(str):
    ''' an item selection object
    '''
    pass


class Loader(syck.Loader):

    __constructs = {}
    
    def register_construct(cls, func, name, tld=None, year=None):
        if tld is not None:
            tld = str(tld)
        if year is not None:
            year = int(year)
        cls.__constructs[(tld,year,name)] = func
    
    register_construct = classmethod(register_construct)

    def construct(self, node):
        if node.tag is not None:
            parts = node.tag.split(':',2)
            if parts[0] == 'tag':
                tld, year = parts[1].split(',')
                year = int(year)
                name = parts[2]
            if parts[0] == 'x-private':
                tld = None
                year = None
                name = parts[1]

            if tld or year or name:
                construct = self.__constructs.get((tld,year,name))
                if construct is not None:
                    return construct(node.value)
        return syck.Loader.construct(self, node)
    
_typeRegistry = {
    ('yaml.org','2002','rest'): rest,
    ('yaml.org','2002','html'): html,
    ('yaml.org','2002','cmsitemsel'): cmsitemsel,
    ('yaml.org','2002','cmsfragment'): cmsfragment,
}

for vartype, factory in _typeRegistry.items():
    Loader.register_construct(factory, vartype[2],tld=vartype[0],year=vartype[1])


