from twisted.python import log
from poop import objstore


class RegisteredUser(objstore.Item):

    __typename__ = 'basiccms/registered_user'
    
    __table__ = 'registered_user'

    first_name = objstore.column()
    surname = objstore.column()
    email = objstore.column()
    optin = objstore.column()

    def __init__(self, *a, **kw):
        first_name = kw.pop('firstName')
        surname = kw.pop('surname')
        comments = kw.pop('comments')
        optin = kw.pop('optin')
        email = kw.pop('email')
        super(RegisteredUser, self).__init__(*a, **kw)
        self.first_name = first_name
        self.surname = surname
        self.email = email
        self.optin = optin
        self.comments = comments

class RegisteredUserManager(object):

    def registerUser(self, sess, firstName, surname, optin, comments, email):

        def handleRegisterFailure(failure):
            log.err(failure)
            return failure

        def flush(res, sess):
            d = sess.flush()
            d.addCallback(lambda ignore: res)
            return d

        d = sess.createItem(RegisteredUser,
            firstName = firstName,
            surname = surname,
            comments = comments,
            optin = optin,
            email = email,
            )

        d.addCallback(flush, sess)
        d.addErrback(handleRegisterFailure)
        return d

    def findMany(self, sess):
        return sess.getItems(itemType=RegisteredUser)

    def removeUser(self, sess, id):
        return sess.removeItem(id)

    def findById(self, sess, id):
        return sess.getItemById(id)

