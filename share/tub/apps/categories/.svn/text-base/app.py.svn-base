from zope.interface import implements

from tub import itub
from tub.apps.categories import web


class CategoriesApplication(object):
    implements(itub.IApplication)

    name = "categories"
    version = 1
    label = "Categories Management"
    description = "Manage the category hierarchy used throughout the system."

    def initialize(self, realm):
        pass

    def getComponents(self):
        return [CategoriesComponent()]


class CategoriesComponent(object):
    implements(itub.IApplicationComponent)

    name = "Categories"
    label = "Categories"
    description = "Manage system categories"

    def resourceFactory(self, avatar, storeSession, segments):
        return web.FacetsPage(avatar), segments
