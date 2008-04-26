import csv
from cStringIO import StringIO
from twisted.internet import defer
from nevow import inevow, loaders, url, static
from poop.objstore import NotFound
import formal

from tub.web import page, util




def loader(filename):
    return loaders.xmlfile(util.resource_filename('basiccms.apps.registeredusers.templates',
        filename), ignoreDocType=True)

class NewUserPage(formal.ResourceMixin, page.Page):

    componentContent = loader('NewUser.html')

    def __init__(self, application):
        super(NewUserPage, self).__init__()
        self.application = application

    def form_user(self, ctx):
        form = formal.Form()
        form.addField('first_name', formal.String(required=True, strip=True), label="First Name")
        form.addField('surname', formal.String(required=True, strip=True))
        form.addField('email', formal.String(required=True, strip=True))
        form.addField('comments', formal.String(), widgetFactory=formal.TextArea)
        form.addField('optin',formal.Boolean(),label='Opt In',description='I would like to be sent information about artwork, artists and exhibitions')
        
        form.addAction(self._submit)
        return form

    def _submit(self, ctx, form, data):

        sess = util.getStoreSession(ctx)

        def userCreated(user):
            return url.URL.fromContext(ctx).sibling(user.id).replace('message', 'User added successfully')

        d = self.application.getManager()
        d.addCallback(lambda manager: manager.registerUser(sess,data['first_name'],data['surname'],data['optin'],data['comments'],data['email']))
        d.addCallback(userCreated)
        return d



class EditUserPage(formal.ResourceMixin, page.Page):

    componentContent = loader('EditUser.html')

    def form_user(self, ctx):
        form = formal.Form()
        form.addField('first_name', formal.String(required=True, strip=True), label="First Name")
        form.addField('surname', formal.String(required=True, strip=True))
        form.addField('email', formal.String(required=True, strip=True))
        form.addField('comments', formal.String(), widgetFactory=formal.TextArea)
        form.addField('optin',formal.Boolean(),label='Opt In',description='I would like to be sent information about artwork, artists and exhibitions')
        form.addAction(self._submit, 'Update User Details' )
        attrs = ('first_name', 'surname', 'comments', 'optin', 'email' )
        form.data = dict((attr,getattr(self.original,attr)) for attr in attrs)
        return form

    def _submit(self, ctx, form, data):
        sess = util.getStoreSession(ctx)

        def userUpdated(user):
            return url.URL.fromContext(ctx).replace('message', 'User updated successfully')

        def updateFailed(failure):
            failure.trap(NotFound)
            util.getStoreSession(ctx).rollbackAlways = True
            return url.URL.fromContext(ctx).replace('errormessage', 'User update failed. Someone else has already changed the user.')

        def update(data):
            self.original.first_name = data['first_name']
            self.original.surname = data['surname']
            self.original.email = data['email']
            self.original.comments = data['comments']
            self.original.optin = data['optin']
            self.original.touch()


        # Don't allow the user name to be changed
        d = defer.Deferred()
        d.addCallback(lambda ignore: update(data))
        d.addCallback(lambda ignore: sess.flush())
        d.addCallback(userUpdated)
        d.addErrback(updateFailed)
        d.callback(None)
        return d


class RegisteredUsersPage(page.Page):
    """Page used for listing users and navigating to user instance editor. Also
    used to create new users and delete.
    """
    componentContent = loader('RegisteredUsers.html')

    def __init__(self, application):
        super(RegisteredUsersPage, self).__init__()
        self.application = application

    def child__submitDelete(self, ctx):
        sess = util.getStoreSession(ctx)

        # Get the list of user ids to delete from the form and
        userids = inevow.IRequest(ctx).args.get('userid')
        if not userids:
            return url.URL.fromContext(ctx)

        def removeUser(manager, id):
            d = manager.removeUser(sess, id)
            d.addCallback(lambda ignore: manager)
            return d

        def usersDeleted(spam):
            return url.URL.fromContext(ctx).replace('message', 'Users deleted successfully')

        d = self.application.getManager()
        for userid in userids:
            d.addCallback(removeUser, userid)
        d.addCallback(lambda spam: sess.flush())
        d.addCallback(usersDeleted)
        return d

    def childFactory(self, ctx, userId):
        # User IDs are always ints
        try:
            userId = int(userId)
        except ValueError:
            return None

        def error(failure):
            failure.trap(objstore.NotFound)
            return None

        sess = util.getStoreSession(ctx)
        d = self.application.getManager()
        d.addCallback(lambda manager: manager.findById(sess, userId))
        return d.addCallback(EditUserPage).addErrback(error)

    def render_newUser(self, ctx, data):
        return ctx.tag(href=url.here.child('new'))

    def data_users(self, ctx, data):
        """Fetch and return a list of registered users known to the system.
        """
        storeSession = util.getStoreSession(ctx)
        d = self.application.getManager()
        d.addCallback(lambda manager: manager.findMany(util.getStoreSession(ctx)))
        return d

    def render_form(self, ctx, user):
        return ctx.tag(action=url.here.child('_submitDelete'))

    def render_user(self, ctx, user):
        """Render a user instance.
        """
        ctx.tag.fillSlots('id', user.id)
        ctx.tag.fillSlots('editLink', url.here.child(user.id))
        ctx.tag.fillSlots('name', '%s %s'%(user.first_name or '', user.surname or ''))
        ctx.tag.fillSlots('optin', user.optin or '')
        ctx.tag.fillSlots('email', user.email or '')
        return ctx.tag

    def child_new(self, ctx):
        return NewUserPage(self.application)

    def render_download_link(self, ctx, data):
        name = 'registered_users.csv'
        return ctx.tag(href=url.URL.fromContext(ctx).child(name))[name]

    def registered_users_csv(self, ctx):

        def gotUsers(users):
            
            fileData = StringIO()
            writer = csv.writer(fileData, dialect="excel")
            for user in users:
                writer.writerow([user.first_name, user.surname, user.optin, user.comments, user.email])

            return static.Data(fileData.getvalue(), 'text/comma-separated-values')

        storeSession = util.getStoreSession(ctx)
        d = self.application.getManager()
        d.addCallback(lambda manager: manager.findMany(util.getStoreSession(ctx)))
        d.addCallback(gotUsers)
        return d

setattr( RegisteredUsersPage, 'child_registered_users.csv', RegisteredUsersPage.registered_users_csv)


