from zope.interface import implements
from nevow import inevow
from tub import itub
from crux import skin

from comments.tub import web
from comments import model, service



class CommentsApplication(object):

    implements(itub.IApplication)

    name = "comments"
    version = 1
    label = "Comments"
    description = "Manage comments posted to the site"
    skin = skin.PackageSkin("comments.tub", "skin")


    def __init__(self, *a, **k):
        super(CommentsApplication, self).__init__(*a, **k)
        self.service = service.CommentsService()


    def initialize(self, realm):
        model.registerTypes(realm.store)


    def getComponents(self):
        return [CommentsComponent(self)]



class CommentsComponent(object):

    implements(itub.IApplicationComponent)

    name = "comments"
    label = "Comments"
    description = "Manage comments"


    def __init__(self, application):
        super(CommentsComponent, self).__init__()
        self.application = application


    def resourceFactory(self, avatar, storeSession, segments):
        return web.CommentsPage(self.application.service, storeSession, avatar), segments

