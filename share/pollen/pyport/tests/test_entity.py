from pollen.pyport import column, entity, error, relation
import unittest
from model import Employee, Department

class BasicTests(unittest.TestCase):
    def test_creation(self):
        # These should work
        Employee()
        Employee(first_name='John')
        Employee(first_name='John', last_name='Smith')
        # This should fail
        try:
            Employee(not_there='blah')
            self.fail('Invalid attribute worked')
        except error.NoSuchAttributeError:
            pass
    def test_attribute_assign(self):
        emp = Employee()
        emp.first_name = 'John'
        self.failIf(emp.first_name != 'John')
        self.failIf(emp._pyport_data['first_name'] != 'John')
        
class DirtyTests(unittest.TestCase):
    def test_00(self):
        emp = Employee()
        self.failIf(emp._pyport_dirty)
    def test_01(self):
        emp = Employee()
        emp.first_name = 'John'
        self.failIf(not emp.is_dirty())
        self.failIf(emp._pyport_dirty_list != {'first_name':1})
    def test_02(self):
        emp = Employee()
        emp.first_name = 'John'
        emp.set_dirty(False)
        self.failIf(emp._pyport_dirty)

unittest.main()

