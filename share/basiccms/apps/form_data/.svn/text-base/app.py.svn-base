from zope.interface import implements
from twisted.internet import defer

from tub import itub
from basiccms.apps.form_data import web
from basiccms.formpage import SubmittedFormData


class FormDataApplication(object):
    implements(itub.IApplication)

    name = "cmsformdata"
    version = 1
    label = "Content Form Data"
    description = "Content Form Data"

    
    def __init__(self):
        pass

    def setParent(self, parent):
        self.parent = parent

    def initialize(self, realm):
        realm.store.registerType(SubmittedFormData)

    def getComponents(self):
        return [FormDataComponent(self)]



class FormDataComponent(object):
    implements(itub.IApplicationComponent)

    name = "cmsformdata"
    label = "Content Form Data"
    description = "Content Form Data"

    def __init__(self, application):
        super(FormDataComponent, self).__init__()
        self.application = application

    def resourceFactory(self, avatar, storeSession, segments):
        return web.FormDataPage(self.application, storeSession), segments

