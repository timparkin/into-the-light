from zope.interface import implements
from twisted.internet import defer

from tub import itub
from basiccms.apps.registeredusers import web, manager

class RegisteredUsersApplication(object):
    implements(itub.IApplication)

    name = "registeredusers"
    version = 1
    label = "Registered Users Management"
    description = "Manage users registered for the newsletter"

    def initialize(self, realm):
        realm.store.registerType(manager.RegisteredUser)

    def getComponents(self):
        return [RegisteredUsersComponent(self)]

    def getManager(self):
        return defer.succeed(manager.RegisteredUserManager())
        


class RegisteredUsersComponent(object):
    implements(itub.IApplicationComponent)

    name = "registeredusers"
    label = "Registered Users"
    description = "Manage users registered for the newsletter"

    def __init__(self, application):
        super(RegisteredUsersComponent, self).__init__()
        self.application = application

    def resourceFactory(self, avatar, segments):
        return web.RegisteredUsersPage(self.application), segments

