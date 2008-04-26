from twisted.cred import portal
from twisted.internet import defer
from nevow import inevow, loaders, rend, url, tags as T, util
from poop.objstore import NotFound
import formal as forms

from tub import capabilities, itub, user
from tub.web import page, util


def loader(filename):
    return loaders.xmlfile(util.resource_filename('tub.apps.users.templates',
        filename), ignoreDocType=True)


def iterRoles(acl):
    from itertools import chain
    roles = iter(acl.root.childRoles)
    while True:
        role = roles.next()
        yield role
        if role.childRoles:
            roles = chain(iter(role.childRoles), roles)


def rolesWidgetFactory(avatar):
    def factory(field):
        roles = [r.name for r in iterRoles(avatar.realm.acl)]
        roleNames = [' - '.join(r.split('.')[1:]) for r in roles]
        options = zip(roles, roleNames)
        return forms.CheckboxMultiChoice(field, options=options)
    return factory


def usernameValidation(data, existing=None, openidEnabled=True):

    def requirePassword():
        if existing is None:
            if not data['password']:
                raise forms.validation.FieldValidationError( 'password required', 'password' )
        elif not existing.password and not data['password']:
                raise forms.validation.FieldValidationError( 'password required', 'password' )

    if not openidEnabled:
        # Need both a username and password
        if not data['username']:
            raise forms.validation.FieldValidationError( 'must specify username', 'username' )
        requirePassword()
    else:
        if not data['openid'] and not data['username']:
            # Need either username or openid or both
            raise forms.validation.FieldValidationError( 'username or openid must be specified', 'openid' )

        if data['username']:
            # If I have a username , I need a password
            requirePassword()


class NewUserPage(forms.ResourceMixin, page.Page):

    componentContent = loader('NewUser.html')

    def form_user(self, ctx):
        avatar = itub.IAvatar(ctx)
        form = forms.Form()
        form.addField('openid', forms.String(strip=True))
        form.addField('username', forms.String(strip=True))
        form.addField('email', forms.String(strip=True))
        form.addField('password', forms.String(), forms.CheckedPassword)
        form.addField('firstName', forms.String(strip=True))
        form.addField('lastName', forms.String(strip=True))
        form.addField('roles', forms.Sequence(forms.String()), rolesWidgetFactory(avatar))
        form.addAction(self._submit)
        return form

    def _submit(self, ctx, form, data):

        usernameValidation(data)

        avatar = itub.IAvatar(ctx)
        sess = util.getStoreSession(ctx)

        def flush(result, sess):
            return sess.flush().addCallback(lambda spam: result)

        def userCreated(user):
            return url.URL.fromContext(ctx).sibling(user.id).replace('message', 'User added successfully')

        def duplicateUser(failure):
            failure.trap(user.UserExistsError)
            sess.forceRollback = True
            raise forms.validation.FieldValidationError( 'duplicate user', 'username' )

        def catchUnauthorizedException(failure):
            failure.trap(capabilities.UnauthorizedException)
            sess.forceRollback = True
            return url.URL.fromContext(ctx).replace('errormessage', 'You do not have permission to create users.')

        d = avatar.getUserManager(sess)
        d.addCallback(lambda userManager: userManager.createUser(**data))
        d.addErrback(duplicateUser)
        d.addCallback(userCreated)
        d.addErrback(catchUnauthorizedException)
        return d


CONTENT_PERMISSIONS = (
    capabilities.CommonPermissions.CREATE,
    capabilities.CommonPermissions.READ,
    capabilities.CommonPermissions.UPDATE,
    capabilities.CommonPermissions.UPDATE_CATEGORIES,
    capabilities.CommonPermissions.UPDATE_METADATA,
    capabilities.CommonPermissions.DELETE,
    capabilities.CommonPermissions.APPROVE,
    capabilities.CommonPermissions.REVOKE,
    )


SYSTEM_OBJECT_PERMISSIONS = (
    capabilities.CommonPermissions.CREATE,
    capabilities.CommonPermissions.UPDATE,
    )


class EditUserPage(forms.ResourceMixin, page.Page):

    componentContent = loader('EditUser.html')

    def form_user(self, ctx):
        avatar = itub.IAvatar(ctx)
        suspendedImmutable = not self.original.testPermission(self.original.setSuspended)
        form = forms.Form()
        form.addField('openid', forms.String(strip=True))
        form.addField('username', forms.String(strip=True))
        form.addField('suspended', forms.Boolean(immutable=suspendedImmutable))
        form.addField('email', forms.String(strip=True))
        form.addField('password', forms.String(), forms.CheckedPassword)
        form.addField('firstName', forms.String(strip=True))
        form.addField('lastName', forms.String(strip=True))
        form.addField('roles', forms.Sequence(forms.String()), rolesWidgetFactory(avatar))
        form.addField('olcount', forms.Integer(), forms.Hidden)
        form.addAction(self._submit, 'Update User Details' )
        attrs = ('openid', 'username', 'email', 'firstName', 'lastName', 'olcount', 'suspended', 'roles')
        form.data = dict((attr,getattr(self.original,attr)) for attr in attrs)
        return form

    def _submit(self, ctx, form, data):

        usernameValidation(data, self.original)

        sess = util.getStoreSession(ctx)

        def updateSuspended():
            suspended = data.get('suspended', None)
            if suspended is None or self.original.suspended == suspended:
                return
            self.original.setSuspended(suspended)

        def userUpdated(user):
#            if data.get('password', None):
#                inevow.ISession(ctx).getComponent(IGuard).updateCredentials(ctx, self.original.username, data.get('password'))

            return url.URL.fromContext(ctx).replace('message', 'User updated successfully')

        def updateFailed(failure):
            failure.trap(NotFound)
            util.getStoreSession(ctx).forceRollback = True
            return url.URL.fromContext(ctx).replace('errormessage', 'User update failed. Someone else has already changed the user.')

        def catchUnauthorizedException(failure):

            failure.trap(capabilities.UnauthorizedException)
            sess.forceRollback = True
            return url.URL.fromContext(ctx).replace('errormessage', 'You do not have permission to update the details of this user.')

        d = defer.Deferred()
        d.addCallback(lambda ignore: self.original.update(data))
        d.addCallback(lambda ignore: updateSuspended())
        d.addCallback(lambda ignore: sess.flush())
        d.addCallback(userUpdated)
        d.addErrback(updateFailed)
        d.addErrback(catchUnauthorizedException)
        d.callback(None)
        return d


class UsersPage(page.Page):
    """Page used for listing users and navigating to user instance editor. Also
    used to create new users and delete.
    """
    componentContent = loader('SiteUsers.html')

    def child_new(self, ctx):
        return NewUserPage()

    def child__submitDelete(self, ctx):
        # Get the list of user ids to delete from the form and
        userids = inevow.IRequest(ctx).args.get('userid')
        if not userids:
            return url.URL.fromContext(ctx)

        def removeUser(userManager, id):
            d = userManager.removeUser(id)
            d.addCallback(lambda ignore: userManager)
            return d

        def usersDeleted(spam):
            return url.URL.fromContext(ctx).replace('message', 'Users deleted successfully')

        def catchUnauthorizedException(failure):
            failure.trap(capabilities.UnauthorizedException)
            sess.forceRollback = True
            return url.URL.fromContext(ctx).replace('errormessage', 'You do not have permission to delete users.')

        avatar = itub.IAvatar(ctx)
        sess = util.getStoreSession(ctx)
        d = avatar.getUserManager(sess)
        for userid in userids:
            d.addCallback(removeUser, userid)
        d.addCallback(lambda spam: sess.flush())
        d.addCallback(usersDeleted)
        d.addErrback(catchUnauthorizedException)
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
        avatar = itub.IAvatar(ctx)
        d = avatar.getUserManager(util.getStoreSession(ctx))
        d.addCallback(lambda userManager: userManager.findById(userId))
        return d.addCallback(EditUserPage).addErrback(error)

    def render_newUser(self, ctx, data):
        return ctx.tag(href=url.here.child('new'))

    def data_users(self, ctx, data):
        """Fetch and return a list of users known to the system.
        """
        avatar = itub.IAvatar(ctx)
        d = avatar.getUserManager(util.getStoreSession(ctx))
        d.addCallback(lambda userManager: userManager.findMany())
        return d

    def render_form(self, ctx, user):
        return ctx.tag(action=url.here.child('_submitDelete'))

    def render_user(self, ctx, user):
        """Render a user instance.
        """
        ctx.tag.fillSlots('id', user.id)
        ctx.tag.fillSlots('editLink', url.here.child(user.id))
        ctx.tag.fillSlots('username', user.username or user.openid)
        ctx.tag.fillSlots('name', user.name or '')
        ctx.tag.fillSlots('email', user.email or '')
        return ctx.tag

