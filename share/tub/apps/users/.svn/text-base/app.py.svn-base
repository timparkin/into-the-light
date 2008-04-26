from zope.interface import implements

from tub import itub
from tub.apps.users import web


class UsersApplication(object):
    implements(itub.IApplication)

    name = "users"
    version = 1
    label = "User Management"
    description = "User and access control management"

    def initialize(self, realm):
        pass

    def getComponents(self):
        return [UsersComponent()]


class UsersComponent(object):
    implements(itub.IApplicationComponent)

    name = "Users"
    label = "System Users"
    description = "Manage users within the system"

    def resourceFactory(self, avatar, storeSession, segments):
        return web.UsersPage(avatar), segments
