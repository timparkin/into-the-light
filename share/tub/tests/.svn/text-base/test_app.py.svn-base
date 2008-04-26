from twisted.trial import unittest

from tub import app


class TestApplication(unittest.TestCase):

    def testApplicationPriority(self):
        app1 = object()
        app2 = object()
        app3 = object()
        app4 = object()
        apps = app.Applications()
        apps.addApplication(app1, 10)
        apps.addApplication(app2, 5)
        apps.addApplication(app3, 85)
        apps.addApplication(app4, 5)
        self.assertEquals(list(apps.iterApplications()), [app2, app4, app1, app3])

    def testComponents(self):
        class PretendComponent(object):
            def __init__(self, name):
                self.name = name
                self.label = name
                self.description = '%s description' % (name,)
            def resourceFactory(avatar, storeSession, segments):
                raise NotImplementedError()
        class PretendApplication(object):
            def __init__(self, name, numComponents):
                self.name = name
                self.version = 1
                self.description = '%s description' % (name,)
                self._numComponents = numComponents
            def getComponents(self):
                return [PretendComponent('%s:comp%d'%(self.name,i)) for i in
                        range(1,self._numComponents+1)]
        apps = app.Applications()
        apps.addApplication(PretendApplication('app1', 1))
        apps.addApplication(PretendApplication('app2', 2))
        apps.addApplication(PretendApplication('app3', 2), priority=1)
        componentNames = [c.name for c in apps.iterComponents()]
        self.assertEquals(componentNames, ['app3:comp1', 'app3:comp2',
            'app1:comp1', 'app2:comp1', 'app2:comp2'])
        self.failUnless(isinstance(apps.componentByName('app2:comp1'),
            PretendComponent))
        self.assertRaises(KeyError, apps.componentByName, 'app9:comp1')
