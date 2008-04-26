from pollen.pyport import column, entity, relation

class IdentityFactory:
    def __init__(self, seq_name):
        self.seq_name = seq_name
    def __call__(self, curs=None, conn=None):
        if curs is None:
            curs = conn.cursor()
        curs.execute("select nextval('%s')" % self.seq_name)
        return (curs.fetchone()[0],)

class Pet(entity.Entity):

    id = column.Integer()
    name = column.String()
    employee_id = column.Integer()

    _pyport_identity = entity.Identity('id', factory=IdentityFactory('pet_id_seq'))
    _pyport_table = 'pet'

class Employee(entity.Entity):

    id = column.Integer()
    first_name = column.String()
    last_name = column.String()
    department_id = column.Integer()
    pets = relation.OneToMany('model.Pet', 'employee_id')

    _pyport_identity = entity.Identity('id', factory=IdentityFactory('employee_id_seq'))
    _pyport_table = 'employee'
    
class Department(entity.Entity):

    id = column.Integer()
    name = column.String()
    employees = relation.OneToMany('model.Employee', 'department_id')

    _pyport_identity = entity.Identity('id', factory=IdentityFactory('department_id_seq'))
    _pyport_table = 'department'
