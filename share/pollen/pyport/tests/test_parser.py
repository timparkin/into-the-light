import unittest
from pollen.pyport import parser

queries = [
    ("from person", ('person',None,None,None)),
    ("from model.Person", ('model.Person',None,None,None)),
    ("from model.Person as p", ('model.Person','p',None,None)),
    ("from model.Person where first_name='Sid'", ('model.Person',None,"first_name='Sid'",None)),
    ("from model.Person as p where p.first_name='Sid'",("model.Person","p","p.first_name='Sid'",None)),
    ("from model.Person order by last_name, first_name",("model.Person",None,None,"last_name, first_name")),
    ("from model.Person as p order by p.first_name",("model.Person","p",None,"p.first_name")),
    ("from model.Person as p where p.first_name='Sid' order by p.first_name",("model.Person","p","p.first_name='Sid'","p.first_name")),
    ]
    
class Tests(unittest.TestCase):

    def setUp(self):
        self.parser = parser.Parser()

    def test(self):
        for q,expected in queries:
            result = self.parser.parse(q)
            self.failIf(list(result) != list(expected))

unittest.main()
