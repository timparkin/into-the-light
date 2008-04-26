import unittest
from pollen.pyport import error, session
import model

create_stmts = [
    '''create sequence department_id_seq''',
    '''create table department (id integer not null, name varchar(200))''',
    '''create sequence employee_id_seq''',
    '''create table employee (id integer not null, first_name varchar(200),
            last_name varchar(200), department_id integer)''',
    '''create sequence pet_id_seq''',
    '''create table pet (id integer not null, name varchar(200), employee_id integer not null)''',
    ]

destroy_stmts = [
    '''drop table pet''',
    '''drop sequence pet_id_seq''',
    '''drop table employee''',
    '''drop sequence employee_id_seq''',
    '''drop table department''',
    '''drop sequence department_id_seq''',
    ]

def make_connection():
    from pyPgSQL import PgSQL
    connect_params = {}
    return PgSQL.connect(**connect_params)

class TestsBase(unittest.TestCase):

    def buildDatabase(self):
        curs = self.conn.cursor()
        for stmt in create_stmts:
            curs.execute(stmt)
        self.conn.commit()

    def destroyDatabase(self):
        curs = self.conn.cursor()
        for stmt in destroy_stmts:
            curs.execute(stmt)
        self.conn.commit()

    def setUp(self):
        self.conn = make_connection()
        self.buildDatabase()
        self.sess = session.Session(self.conn)

    def tearDown(self):
        self.sess.close()
        del self.sess
        self.conn.rollback()
        self.destroyDatabase()
        self.conn.close()

class BasicTests(TestsBase):

    def test_00_save(self):
        p = model.Employee(first_name='John', last_name='Smith')
        self.sess.save(p)
        self.sess.flush()

    def test_01_load(self):
        p = model.Employee(first_name='John', last_name='Smith')
        self.sess.save(p)
        self.sess.flush()
        p = self.sess.load(model.Employee, (p.id,))

    def test_02_update(self):
        p = model.Employee(first_name='John', last_name='Smith')
        self.sess.save(p)
        self.sess.flush()
        p = self.sess.load(model.Employee, (p.id,))
        p.first_name = 'Tim'
        p.last_name = 'Parkin'
        self.failIf(len(self.sess.updates) != 1)
        self.sess.flush()
        self.sess.flush()

    def test_03_delete(self):
        p = model.Employee(first_name='John', last_name='Smith')
        self.sess.save(p)
        self.sess.flush()
        p = self.sess.load(model.Employee, (p.id,))
        self.sess.remove(p)
        self.sess.flush()
        self.sess.flush()

class SessionJoinTests(TestsBase):

    def test_01_join(self):
        p = model.Employee(first_name='John', last_name='Smith')
        self.sess.save(p)
        self.sess.flush()
        p = self.sess.load(model.Employee, (p.id,))
        self.sess.close()
        del self.sess
        p.first_name = 'Tim'
        p.last_name = 'Parkin'
        self.sess = session.Session(self.conn)
        self.sess.join(p)
        self.sess.flush()

    def test_02_join_new(self):
        '''Test that joining a new object fails'''
        p = model.Employee(first_name='John', last_name='Smith')
        try:
            self.sess.join(p)
            self.fail('join with new object should fail')
        except error.Error:
            pass
        
class FindTests(TestsBase):

    def test_01_find(self):
        p = model.Employee(first_name='John', last_name='Smith')
        self.sess.save(p)
        self.sess.flush()
        ps = self.sess.find('from model.Employee')
        self.failIf(len(list(ps)) != 1)
        self.sess.save(model.Employee(first_name='Bill', last_name='Smith'))
        self.sess.flush()
        ps = self.sess.find('from model.Employee')
        self.failIf(len(list(ps)) != 2)
        ps = self.sess.find("from model.Employee as person where person.first_name='John'")
        self.failIf(len(list(ps)) != 1)
        ps = self.sess.find("from model.Employee as person where person.last_name='Smith'")
        self.failIf(len(list(ps)) != 2)
        ps = self.sess.find("from model.Employee as person where person.first_name='Wibble'")
        self.failIf(len(list(ps)) != 0)

    def test_02(self):
        '''Test find using separate params'''
        self.sess.save(model.Employee(first_name='John', last_name='Smith'))
        self.sess.flush()
        l = list(self.sess.find("from model.Employee as e where e.first_name=%s", 'John'))
        self.failIf(len(l) != 1)

class RelationTests(TestsBase):
    
    def setUp(self):
        TestsBase.setUp(self)
        d = model.Department(name='Engineering')
        d.employees.append(
                model.Employee(first_name='John', last_name='Smith'))
        d.employees.append(
                model.Employee(first_name='Bill', last_name='Smith'))
        self.sess.save(d)
        self.sess.flush()

    def test_01(self):
        '''Just to test that the overridden setUp is adding data correctly'''
        self.failIf(len(list(self.sess.find('from model.Department'))) != 1)
        self.failIf(len(list(self.sess.find('from model.Employee'))) != 2)

    def test_02(self):
        '''Test lazy fetching of relations'''
        d = self.sess.load(model.Department, (1))
        self.failIf(len(d.employees) != 2)
        
    def test_03(self):
        '''Test deletion of a collection item'''
        d = self.sess.load(model.Department, (1))
        del d.employees[0]
        self.sess.flush()
        d = self.sess.load(model.Department, (1))
        self.failIf(len(d.employees) != 1)
        
    def test_04(self):
        '''Test deletion of a collection item'''
        d = self.sess.load(model.Department, (1))
        del d.employees[:]
        self.sess.flush()
        d = self.sess.load(model.Department, (1))
        self.failIf(len(d.employees) != 0)

    def test_05(self):
        '''Test saving collections 2 deep'''
        d = model.Department(name='Marketing')
        d.employees.append(model.Employee(first_name='Kate', last_name='Watkins'))
        d.employees.append(model.Employee(first_name='Sam', last_name='Reece'))
        d.employees[0].pets.append(model.Pet(name='Fluffy'))
        d.employees[0].pets.append(model.Pet(name='Flipper'))
        self.sess.save(d)
        self.sess.flush()
        d = self.sess.load(model.Department, d.id)
        self.failIf(len(d.employees[0].pets) != 2)
        for employee in d.employees:
            if employee.first_name == 'Kate':
                self.failIf(len(employee.pets) != 2)
            if employee.first_name == 'Sam':
                self.failIf(len(employee.pets) != 0)

    def test_06(self):
        '''Test changes to nested collection'''
        d = model.Department(name='Marketing')
        d.employees.append(model.Employee(first_name='Kate', last_name='Watkins'))
        d.employees[0].pets.append(model.Pet(name='Fluffy'))
        self.sess.save(d)
        self.sess.flush()
        d = self.sess.load(model.Department, d.id)
        d.employees[0].pets.append(model.Pet(name='Flipper'))
        self.sess.flush()
        d = self.sess.load(model.Department, d.id)
        self.failIf(len(d.employees[0].pets) != 2)
        d = self.sess.load(model.Department, d.id)
        del d.employees[0].pets[0]
        self.sess.flush()
        d = self.sess.load(model.Department, d.id)
        self.failIf(len(d.employees[0].pets) != 1)
        
    def test_07_assign_self(self):
        """Test that assigning itself doesn't change anything"""
        d = self.sess.load(model.Department, 1)
        d.employees = d.employees
        self.sess.flush()
        d2 = self.sess.load(model.Department, 1)
        self.failIf([e.id for e in d.employees] != [e.id for e in d2.employees])
        
    def test_08_assign_none(self):
        self.fail('Not implemented')


class CacheTests(TestsBase):

    def test_01_save_and_load(self):
        p = model.Employee(first_name='John', last_name='Smith')
        self.sess.save(p)
        self.sess.flush()
        identity = (p.id,)
        p1 = self.sess.load(model.Employee, identity)
        self.assertEquals(id(p ), id(p1))
        
    def test_01_load_multiple(self):
        p = model.Employee(first_name='John', last_name='Smith')
        self.sess.save(p)
        self.sess.flush()
        identity = (p.id,)
        p1 = self.sess.load(model.Employee, identity)
        p2 = self.sess.load(model.Employee, identity)
        self.assertEquals(id(p1), id(p2))
        
    def test_01_find(self):
        p = model.Employee(first_name='John', last_name='Smith')
        self.sess.save(p)
        self.sess.flush()
        p1 = list(self.sess.find('from model.Employee'))[0]
        p2 = list(self.sess.find('from model.Employee'))[0]
        self.assertEquals(id(p1), id(p2))
        

unittest.main()
